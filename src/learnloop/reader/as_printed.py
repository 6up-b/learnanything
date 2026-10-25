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
  joined only while the union holds no other block's centre, so a
  neighbouring exercise, solution or worked example that sits between two of
  the problem's blocks splits the crop rather than showing in it. The rule is
  structural (a centre inside a rectangle): no padding, no tolerance
  constant. A block without a page or a box crops nothing, and a crop that
  cannot be made is reported as such, never replaced by the whole page.
* **The cold rule** (D46, spec G61). During a check on your own the view
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
from dataclasses import dataclass
from typing import Any

from learnloop.ingest.ir import DocumentBlock, is_figure_block

#: The kinds of view (the client renders one control per kind).
KIND_PAGE = "page"
KIND_FIGURE = "figure"
KIND_PHOTO = "photo"
KIND_NONE = "none"

FIGURE_LABEL = "the figure, as printed"
PHOTO_LABEL = "your photo"
NO_ORIGINAL = "the page image isn't available for this book · the transcription is above"

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


def _holds_centre(box: Box, other: Box) -> bool:
    x = (other[0] + other[2]) / 2
    y = (other[1] + other[3]) / 2
    return box[0] < x < box[2] and box[1] < y < box[3]


def crop_boxes(
    own: Sequence[DocumentBlock], neighbours: Sequence[DocumentBlock]
) -> tuple[list[CropBox], list[str]]:
    """The crops of ``own`` (the problem's blocks) in reading order, and the
    span ids that crop nothing (no page or no box). ``neighbours`` are the
    blocks on the same pages; the problem's own are ignored among them."""

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
        if current is not None and current.page == page:
            merged = _union(current.bbox, box)
            if not any(_holds_centre(merged, other) for other in others.get(page, [])):
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


def printed_crops(
    repository: Any,
    *,
    extraction_id: str,
    span_ids: Sequence[str],
    render: bool,
    figure_only: bool = False,
) -> dict[str, Any]:
    """The crops of these blocks (the multi-block form of
    ``reader.block_original_region``). ``status``: ``ok``; ``no_original``
    (geometry, but no readable local PDF, or no crop could be made);
    ``no_geometry`` (no block with a page and a box); ``not_found``.
    ``figure_only`` keeps only figure blocks and strips every locator."""

    blocks = repository.document_blocks(extraction_id, [str(span) for span in span_ids])
    if figure_only:
        blocks = [block for block in blocks if is_figure_block(block)]
    if not blocks:
        return {"status": "not_found", "crops": [], "skipped_span_ids": []}
    pages = {int(block.page) for block in blocks if block.page is not None}
    neighbours = repository.document_blocks_on_pages(extraction_id, sorted(pages)) if pages else []
    boxes, skipped = crop_boxes(blocks, neighbours)
    if not boxes:
        return {"status": "no_geometry", "crops": [], "skipped_span_ids": skipped}
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


def item_as_printed(
    repository: Any,
    item: Any,
    *,
    enabled: bool,
    cold: bool,
    render: bool,
    source_title: str | None = None,
    photo: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """The practice view of ``item`` as printed (K15). ``cold``: a check on
    your own now (the caller reads it on the server, D46); ``photo``: the
    capture the card was written from, when there is one."""

    if not enabled:
        return {"enabled": False, "kind": KIND_NONE, "cold": cold, "reason": "disabled"}
    canonical = getattr(item, "canonical_exercise", None)
    if canonical is not None:
        if canonical.relation != "verbatim":
            return _none("variant", cold=cold)
        if cold:
            figures = printed_crops(repository, extraction_id=canonical.extraction_id,
                                    span_ids=canonical.span_ids, render=render, figure_only=True)
            if not figures["crops"]:
                return _none("cold_check", cold=True)
            return {"enabled": True, "kind": KIND_FIGURE, "cold": True, "label": FIGURE_LABEL,
                    "status": figures["status"], "crops": figures["crops"]}
        printed = printed_crops(repository, extraction_id=canonical.extraction_id,
                                span_ids=canonical.span_ids, render=render)
        if not printed["crops"]:
            return _none(printed["status"], cold=False)
        first = printed["crops"][0]
        title = source_title or "your book"
        label = f"as printed ({title} p.{first['page_label']})"
        on_first_page = [span for crop in printed["crops"] if crop["page"] == first["page"]
                         for span in crop["span_ids"]]
        view: dict[str, Any] = {
            "enabled": True, "kind": KIND_PAGE, "cold": False, "label": label,
            "status": printed["status"], "crops": printed["crops"],
            "locator": {"source_title": source_title, "exercise_label": canonical.label,
                        "page_label": first["page_label"]},
            "transcription_report": True,
            "original_page": None,
        }
        if printed["status"] == "ok":
            view["original_page"] = {"extraction_id": canonical.extraction_id, "span_id": first["span_ids"][0],
                                     "outline_span_ids": on_first_page}
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
    "FIGURE_LABEL", "KIND_FIGURE", "KIND_NONE", "KIND_PAGE", "KIND_PHOTO", "NO_ORIGINAL", "PHOTO_LABEL",
    "CropBox", "crop_boxes", "item_as_printed", "page_label", "printed_crops",
]
