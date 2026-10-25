"""Reader CA1: the problem as printed (ux_reader_compare_ask_v1 §8; K15, C10).

A problem imported from a page shows *as printed*: a crop of only its own
blocks from the page, so the learner can check the transcription against the
book without leaving it; and *original page*, the whole page (before Submit
it is the book left open, one hint-equivalent, which the practice screen
counts in the existing book component of ``hints_used``: no new evidence
meaning, spec §5.4). A card written from a phone photo shows *your photo*.

The rules held here, on the server:

* **Only the problem's own blocks** (C10). A crop is the union of the
  problem's own boxes on one page, in reading order. Consecutive blocks are
  joined only while the joined rectangle shows no more of any other block
  than the two parts already did (Codex review F2: the test is the area of
  every other block inside the rectangle, not its centre, so a neighbour
  that only reaches into the gap still splits the crop). The rule is
  structural (areas compared exactly): no padding, no tolerance constant. A
  block without a page or a box crops nothing, and a crop that cannot be
  made is reported as such, never replaced by the whole page; the original
  page is still offered when the block's page is known (F5).
* **Where the print comes from** (§8.4, §12.4): a ``canonical_exercise``
  (the sources service's import), or a Reader selection import
  (``reader.import_exercise`` and the workbench's "work through this": its
  ``learner_item_authored`` event marks it, its ``block_span_v1`` source
  refs name the blocks, Codex review F4). A learner-drawn sub-box stored on
  a source ref (``region``) is the crop shown for that block, clipped to the
  block's own box.
* **The cold rule** (D46, spec G61). During a check on your own (a due
  "Check once", a cold follow-up, an active diagnostic presentation; the
  caller reads which, F1) the view
  carries no locator, page, label, link, photo or crop, except the
  figure-only exception (§15 Q10): a figure block the problem was imported
  with is part of its stimulus, so it is cropped to the figure alone, with
  no caption, number, page or box.
* **A variant is not the book's problem.** An item varied from a textbook
  exercise (``relation = "variant_of"``) has no print of its own: none is
  shown (the parent's print would be another problem, and its neighbours).
* **No exposure, no model call.** The crop is the stem the learner already
  has, so nothing is recorded; the original page records its exposure where
  it opens (``get_span_view``), as every source opening does.

``practice.as_printed.enabled`` off: no view (every screen as before CA1).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from learnloop.ingest.ir import DocumentBlock, is_figure_block, page_region, selection_region

#: The kinds of view (the client renders one control per kind).
KIND_PAGE = "page"
KIND_FIGURE = "figure"
KIND_PHOTO = "photo"
KIND_NONE = "none"

FIGURE_LABEL = "the figure, as printed"
PHOTO_LABEL = "your photo"
NO_ORIGINAL = "the page image isn't available for this book · the transcription is above"
#: F5: the page is known and readable, but no block has a box to crop.
NO_CROP = "the crop isn't available for this problem · the original page is"

Box = tuple[float, float, float, float]


@dataclass(frozen=True)
class CropBox:
    """One crop: the union of consecutive own blocks on one page."""

    page: int
    bbox: Box
    span_ids: tuple[str, ...]


def _box(block: DocumentBlock) -> Box | None:
    bbox = block.bbox
    if not bbox or len(bbox) != 4:
        return None
    try:
        x0, y0, x1, y1 = (float(value) for value in bbox)
    except (TypeError, ValueError):
        return None
    left, right = sorted((x0, x1))
    top, bottom = sorted((y0, y1))
    if right <= left or bottom <= top:
        return None
    return (left, top, right, bottom)


def _union(a: Box, b: Box) -> Box:
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def _overlap(a: Box, b: Box) -> Box | None:
    left, top = max(a[0], b[0]), max(a[1], b[1])
    right, bottom = min(a[2], b[2]), min(a[3], b[3])
    return (left, top, right, bottom) if right > left and bottom > top else None


def _area(box: Box | None) -> Fraction:
    if box is None:
        return Fraction(0)
    return (Fraction(box[2]) - Fraction(box[0])) * (Fraction(box[3]) - Fraction(box[1]))


def _shows_more_of(merged: Box, current: Box, box: Box, other: Box) -> bool:
    """Whether the joined rectangle shows any of ``other`` that neither part
    showed: its area inside ``merged`` against its area inside the two parts
    (inclusion-exclusion over two rectangles), compared exactly."""

    in_current, in_box = _overlap(other, current), _overlap(other, box)
    in_both = _overlap(in_current, in_box) if in_current is not None and in_box is not None else None
    inside_parts = _area(in_current) + _area(in_box) - _area(in_both)
    return _area(_overlap(other, merged)) > inside_parts


def _clip(region: Box, block_box: Box) -> Box | None:
    """A learner-drawn sub-box, clipped to the block's own box (RW5a's rule)."""

    return _overlap(region, block_box)


def crop_boxes(
    own: Sequence[DocumentBlock],
    neighbours: Sequence[DocumentBlock],
    regions: Mapping[str, tuple[int, Box]] | None = None,
) -> tuple[list[CropBox], list[str]]:
    """The crops of ``own`` (the problem's blocks) in reading order, and the
    span ids that crop nothing (no page or no box). ``neighbours`` are the
    blocks on the same pages; the problem's own are ignored among them.
    ``regions``: a learner-drawn sub-box per span (page, box), used in place
    of that block's box (clipped to it; a region on another page is ignored)."""

    own_ids = {block.span_id for block in own}
    others: dict[int, list[Box]] = {}
    for block in neighbours:
        if block.span_id in own_ids or block.page is None:
            continue
        box = _box(block)
        if box is not None:
            others.setdefault(int(block.page), []).append(box)
    crops: list[CropBox] = []
    skipped: list[str] = []
    current: CropBox | None = None
    for block in sorted(own, key=lambda candidate: candidate.ordinal):
        box = _box(block)
        if block.page is None or box is None:
            skipped.append(block.span_id)
            continue
        page = int(block.page)
        region = (regions or {}).get(block.span_id)
        if region is not None and int(region[0]) == page:
            clipped = _clip(region[1], box)
            if clipped is None:
                skipped.append(block.span_id)
                continue
            box = clipped
        if current is not None and current.page == page:
            merged = _union(current.bbox, box)
            if not any(_shows_more_of(merged, current.bbox, box, other) for other in others.get(page, [])):
                current = CropBox(page, merged, (*current.span_ids, block.span_id))
                continue
        if current is not None:
            crops.append(current)
        current = CropBox(page, box, (block.span_id,))
    if current is not None:
        crops.append(current)
    return crops, skipped


def _pdf_path(repository: Any, extraction_id: str) -> Any:
    from learnloop.reader import span_view as SV

    try:
        return SV._original_pdf_for(repository, extraction_id)
    except Exception:  # noqa: BLE001 - an unresolvable original is "no original", never an error
        return None


def page_label(pdf_path: Any, page: int | None) -> str | None:
    """The printed page label when the PDF carries page labels, else the
    page's position in the file (one-based); None without a page."""

    if page is None:
        return None
    from learnloop.reader import span_view as SV

    return SV._local_pdf_page_label(pdf_path, page) or str(int(page) + 1)


@dataclass(frozen=True)
class PrintedOrigin:
    """Where an item's print is: its blocks on one extraction (§8.4)."""

    extraction_id: str
    span_ids: tuple[str, ...]
    source_id: str | None = None
    label: str | None = None
    relation: str = "verbatim"
    #: A learner-drawn sub-box per span (page, box), §12.4.
    regions: Mapping[str, tuple[int, Box]] = field(default_factory=dict)
    #: The blocks that locate the original page, when they are more than
    #: ``span_ids`` (the crop's own blocks): a selection split into several
    #: exercises names every block it was imported from here, and only this
    #: item's own in ``span_ids`` (empty when that can't be read: no free
    #: crop, the charged page only; Codex re-review F9). None: ``span_ids``.
    page_span_ids: tuple[str, ...] | None = None

    @property
    def located_by(self) -> tuple[str, ...]:
        return self.span_ids if self.page_span_ids is None else self.page_span_ids


def _region(value: Any) -> tuple[int, Box] | None:
    return page_region(dict(value)) if isinstance(value, Mapping) else None


def region_for(value: Mapping[str, Any] | None, span_ids: Sequence[str]) -> dict[str, tuple[int, Box]]:
    """A selection's ``region`` as :func:`crop_boxes` takes it (``ingest.ir.selection_region``)."""

    return selection_region(dict(value), span_ids) if isinstance(value, Mapping) else {}


def _ref_field(ref: Any, name: str) -> Any:
    if isinstance(ref, Mapping):
        return ref.get(name)
    value = getattr(ref, name, None)
    if value is None:
        extra = getattr(ref, "model_extra", None) or {}
        value = extra.get(name)
    return value


def _selection_origin(repository: Any, item: Any) -> PrintedOrigin | None:
    """A Reader selection import (``reader.import_exercise``, the workbench's
    "work through this"): marked by its ``learner_item_authored`` event (the
    origin alone is shared with AI proposals over sources), its blocks named
    by its ``block_span_v1`` source refs, else by its import rows."""

    from learnloop.db.stores.source_service import imports_for_item, is_reader_import
    from learnloop.ingest.locators import parse_block_span

    provenance = getattr(item, "provenance", None)
    if getattr(provenance, "origin", None) != "canonical_extract":
        return None
    with repository.connection() as connection:
        if not is_reader_import(connection, item.id):
            return None
        rows = [row for row in imports_for_item(connection, item.id) if row.get("caller") == "reader"]
    extraction_id: str | None = None
    spans: list[str] = []
    #: Re-review F9: ``owned`` per block of a split selection (absent: unsplit).
    ownership: dict[str, bool] = {}
    regions: dict[str, tuple[int, Box]] = {}
    source_id: str | None = None
    for ref in getattr(provenance, "source_refs", None) or []:
        if _ref_field(ref, "ref_type") != "canonical_source":
            continue
        parsed = parse_block_span(str(_ref_field(ref, "locator") or ""))
        if parsed is None:
            continue
        ref_extraction, span = parsed
        if extraction_id is None:
            extraction_id = ref_extraction
        if ref_extraction != extraction_id or span in spans:
            continue
        spans.append(span)
        owned = _ref_field(ref, "owned")
        if isinstance(owned, bool):
            ownership[span] = owned
        ref_id = _ref_field(ref, "ref_id")
        source_id = source_id or _ref_field(ref, "source_id") or (str(ref_id) if ref_id and ref_id != ref_extraction else None)
        region = _region(_ref_field(ref, "region"))
        if region is not None:
            regions[span] = region
    if extraction_id is None and rows:
        extraction_id = str(rows[-1]["extraction_id"])
        spans = [str(span) for span in rows[-1].get("span_ids") or []]
        source_id = rows[-1].get("source_id")
    if extraction_id is None or not spans:
        return None
    if source_id is None and rows:
        source_id = rows[-1].get("source_id")
    if ownership:
        own = tuple(span for span in spans if ownership.get(span, False))
    elif _split_import(repository, item.id, rows):
        own = ()                                       # split before ownership was kept: no free crop
    else:
        return PrintedOrigin(extraction_id=extraction_id, span_ids=tuple(spans), source_id=source_id,
                             regions=regions)
    return PrintedOrigin(extraction_id=extraction_id, span_ids=own, source_id=source_id,
                         regions={span: box for span, box in regions.items() if span in own},
                         page_span_ids=tuple(spans))


def _split_import(repository: Any, item_id: str, rows: Sequence[Mapping[str, Any]]) -> bool:
    """Whether the selection this item was imported from also became other
    items (Codex re-review F9): the Reader's import writes one row per item,
    in one write, with the selection's blocks; another item's row from that
    same write means the selection was split, and which blocks are whose is
    not recorded."""

    if not rows:
        return False
    import json

    last = rows[-1]
    with repository.connection() as connection:
        siblings = connection.execute(
            "SELECT span_ids_json FROM source_exercise_imports WHERE caller = 'reader' AND extraction_id = ? "
            "AND created_at = ? AND practice_item_id IS NOT NULL AND practice_item_id != ?",
            (str(last["extraction_id"]), last["created_at"], item_id)).fetchall()
    own = list(last.get("span_ids") or [])
    for (raw,) in siblings:
        try:
            if json.loads(raw or "[]") == own:
                return True
        except (TypeError, ValueError):
            return True                                # unreadable: treated as split (fails closed)
    return False


def printed_origin(repository: Any, item: Any) -> PrintedOrigin | None:
    """The item's print, or None (pasted text, a generated card, a photo card)."""

    canonical = getattr(item, "canonical_exercise", None)
    if canonical is not None:
        return PrintedOrigin(extraction_id=canonical.extraction_id, span_ids=tuple(canonical.span_ids),
                             source_id=canonical.source_id, label=canonical.label, relation=canonical.relation)
    if repository is None:
        return None
    try:
        return _selection_origin(repository, item)
    except Exception:  # noqa: BLE001 - an unreadable origin shows no print, never an error
        import logging

        logging.getLogger(__name__).exception("Could not read where %s was imported from", getattr(item, "id", "?"))
        return None


def printed_crops(
    repository: Any,
    *,
    extraction_id: str,
    span_ids: Sequence[str],
    render: bool,
    figure_only: bool = False,
    regions: Mapping[str, tuple[int, Box]] | None = None,
) -> dict[str, Any]:
    """The crops of these blocks (the multi-block form of
    ``reader.block_original_region``). ``status``: ``ok``; ``no_original``
    (geometry, but no readable local PDF, or no crop could be made);
    ``no_geometry`` (no block with a page and a box); ``not_found``.
    ``figure_only`` keeps only figure blocks and strips every locator.
    ``regions``: learner-drawn sub-boxes (:func:`crop_boxes`)."""

    blocks = repository.document_blocks(extraction_id, [str(span) for span in span_ids])
    if figure_only:
        blocks = [block for block in blocks if is_figure_block(block)]
    if not blocks:
        return {"status": "not_found", "crops": [], "skipped_span_ids": []}
    pages = {int(block.page) for block in blocks if block.page is not None}
    neighbours = repository.document_blocks_on_pages(extraction_id, sorted(pages)) if pages else []
    boxes, skipped = crop_boxes(blocks, neighbours, regions)
    if not boxes:
        return {"status": "no_geometry", "crops": [], "skipped_span_ids": [] if figure_only else skipped}
    pdf_path = _pdf_path(repository, extraction_id)
    images: list[str | None] = [None for _ in boxes]
    status = "ok" if pdf_path is not None else "no_original"
    if render and pdf_path is not None:
        from learnloop.reader import span_view as SV

        by_page: dict[int, list[int]] = {}
        for index, box in enumerate(boxes):
            by_page.setdefault(box.page, []).append(index)
        for page, indices in by_page.items():
            made, _size = SV._local_pdf_crops(pdf_path, page, [list(boxes[i].bbox) for i in indices])
            for index, image in zip(indices, made):
                images[index] = image
        if not any(images):
            status = "no_original"
    if figure_only:
        crops = [{"index": index, "image": image} for index, image in enumerate(images)]
        return {"status": status, "crops": crops, "skipped_span_ids": []}
    crops = []
    for box, image in zip(boxes, images):
        crops.append({
            "page": box.page,
            "page_label": page_label(pdf_path, box.page),
            "bbox": list(box.bbox),
            "span_ids": list(box.span_ids),
            "image": image,
        })
    return {"status": status, "crops": crops, "skipped_span_ids": skipped}


def _none(reason: str, *, cold: bool) -> dict[str, Any]:
    return {"enabled": True, "kind": KIND_NONE, "cold": cold, "reason": reason}


def _page_only(repository: Any, origin: PrintedOrigin) -> tuple[int, str, list[str]] | None:
    """F5: the first page of the problem's blocks and its blocks there, when
    no crop can be made but the page is known (a pypdf extraction keeps a
    page and no box); None without a page."""

    blocks = repository.document_blocks(origin.extraction_id, list(origin.located_by))
    paged = [block for block in blocks if block.page is not None]
    if not paged:
        return None
    page = int(paged[0].page)
    return page, paged[0].span_id, [block.span_id for block in paged if int(block.page) == page]


def _page_without_crop(repository: Any, origin: PrintedOrigin, *, source_title: str | None,
                       cold: bool) -> dict[str, Any]:
    """F5 and re-review F9: no crop can be made (no box, or the problem's own
    blocks are not known), but a known page of a readable original is still
    the book's page: offered (with its cost, where it opens), and the crop
    says honestly that it can't be made. Cold: nothing."""

    if cold:
        return _none("cold_check", cold=True)
    paged = _page_only(repository, origin)
    pdf_path = _pdf_path(repository, origin.extraction_id) if paged is not None else None
    if paged is None or pdf_path is None:
        return _none("no_geometry", cold=False)
    page, first_span, on_page = paged
    label_text = page_label(pdf_path, page)
    return {
        "enabled": True, "kind": KIND_PAGE, "cold": False,
        "label": f"as printed ({source_title or 'your book'} p.{label_text})",
        "status": "no_geometry", "crops": [],
        "locator": {"source_title": source_title, "exercise_label": origin.label, "page_label": label_text},
        "transcription_report": True,
        "original_page": {"extraction_id": origin.extraction_id, "span_id": first_span,
                          "outline_span_ids": on_page, "source_id": origin.source_id},
        "notice": NO_CROP,
    }


def item_as_printed(
    repository: Any,
    item: Any,
    *,
    enabled: bool,
    cold: bool,
    render: bool,
    source_title: str | None = None,
    photo: Mapping[str, Any] | None = None,
    origin: PrintedOrigin | None = None,
) -> dict[str, Any]:
    """The practice view of ``item`` as printed (K15). ``cold``: a check on
    your own now (the caller reads it on the server, D46); ``photo``: the
    capture the card was written from, when there is one; ``origin``: where
    its print is (read here when not given, :func:`printed_origin`)."""

    if not enabled:
        return {"enabled": False, "kind": KIND_NONE, "cold": cold, "reason": "disabled"}
    if origin is None:
        origin = printed_origin(repository, item)
    if origin is not None:
        if origin.relation != "verbatim":
            return _none("variant", cold=cold)
        if not origin.span_ids:
            return _page_without_crop(repository, origin, source_title=source_title, cold=cold)
        if cold:
            figures = printed_crops(repository, extraction_id=origin.extraction_id, span_ids=origin.span_ids,
                                    render=render, figure_only=True, regions=origin.regions)
            if not figures["crops"]:
                return _none("cold_check", cold=True)
            return {"enabled": True, "kind": KIND_FIGURE, "cold": True, "label": FIGURE_LABEL,
                    "status": figures["status"], "crops": figures["crops"]}
        printed = printed_crops(repository, extraction_id=origin.extraction_id, span_ids=origin.span_ids,
                                render=render, regions=origin.regions)
        title = source_title or "your book"
        if not printed["crops"]:
            if printed["status"] != "no_geometry":
                return _none(printed["status"], cold=False)
            return _page_without_crop(repository, origin, source_title=source_title, cold=False)
        first = printed["crops"][0]
        label = f"as printed ({title} p.{first['page_label']})"
        on_first_page = [span for crop in printed["crops"] if crop["page"] == first["page"]
                         for span in crop["span_ids"]]
        view: dict[str, Any] = {
            "enabled": True, "kind": KIND_PAGE, "cold": False, "label": label,
            "status": printed["status"], "crops": printed["crops"],
            "locator": {"source_title": source_title, "exercise_label": origin.label,
                        "page_label": first["page_label"]},
            "transcription_report": True,
            "original_page": None,
        }
        if printed["status"] == "ok":
            view["original_page"] = {"extraction_id": origin.extraction_id, "span_id": first["span_ids"][0],
                                     "outline_span_ids": on_first_page, "source_id": origin.source_id}
        else:
            view["notice"] = NO_ORIGINAL
        return view
    if photo is not None:
        if cold:
            return _none("cold_check", cold=True)
        return {"enabled": True, "kind": KIND_PHOTO, "cold": False, "label": PHOTO_LABEL,
                "photo": {"capture_id": photo["capture_id"], "captured_at": photo.get("captured_at")}}
    return _none("no_print", cold=cold)


__all__ = [
    "FIGURE_LABEL", "KIND_FIGURE", "KIND_NONE", "KIND_PAGE", "KIND_PHOTO", "NO_CROP", "NO_ORIGINAL", "PHOTO_LABEL",
    "CropBox", "PrintedOrigin", "crop_boxes", "item_as_printed", "page_label", "printed_crops", "printed_origin",
    "region_for",
]
