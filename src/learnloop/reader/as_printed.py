"""Reader CA1: the problem as printed (ux_reader_compare_ask_v1 §8; K15, C10).

A problem imported from a page shows *as printed*: a crop of only its own
blocks from the page, so the learner can check the transcription against the
book without leaving it; and *original page*, the whole page (before Submit
it is the book left open, one hint-equivalent, which the practice screen
counts in the existing book component of ``hints_used``: no new evidence
meaning, spec §5.4). A card written from a phone photo shows *your photo*.

The rules held here, on the server:

* **Only the problem's own blocks** (C10), **one crop per block**. Each
  retained region (a text block's box, or a figure's box clipped to the
  learner's selected sub-box) is its own crop, in reading order, never
  merged with another (the Astra redesign, F6: a union rectangle can take in
  pixels of a block or sub-box that was left out). Boxes can still overlap,
  so every rendered crop is **masked** (Sol verify 3): each crop is painted
  white over every excluded area it overlaps, which is every block on the
  page not retained (a dropped solution, a neighbour, an owned figure held
  back) and, for a retained block shown by its selected sub-box, the rest
  of its box. No crop then shows a pixel of excluded content, whatever
  overlaps; a retained box loses only what it shares with excluded content.
  An excluded box holding a whole crop is that block's container (a figure
  group around its figure) and is not painted over it. The DTO is
  unchanged. No padding, no tolerance constant. A
  block without a page or a box crops nothing, and a crop that cannot be
  made is reported as such, never replaced by the whole page; the original
  page is still offered when the block's page is known (F5).
* **Where the print comes from** (§8.4, §12.4): a ``canonical_exercise``
  (the sources service's import), or a Reader selection import
  (``reader.import_exercise`` and the workbench's "work through this": its
  ``learner_item_authored`` event marks it, its ``block_span_v1`` source
  refs name the blocks, Codex review F4). A learner-drawn sub-box stored on
  a source ref (``region``) is the crop shown for that block, clipped to the
  block's own box. Each ref of a selection import says whether that block
  is this item's own (``owned``), and only those are cropped; where that is
  not known (a selection-level edit, or an import written before the mark)
  no crop is free, and the original page (one hint before Submit) is still
  offered (Codex re-review F9).
* **Only the problem, never the solution** (Astra batch review; owner
  2026-10-26: "i would hope that crop excludes the solution"). The free crop
  is conservative by construction (the Astra redesign):

  1. *Solution blocks leave.* A block on the import's book-solution spans,
     with a ``solution`` effective role, or (a text block) led by a
     "Solution" heading (:data:`_ANSWER_HEADING`) is never cropped and never
     outlined on the original page, whatever the marks say. A figure leaves
     only by its span, its role, or its validated figure role (Sol verify 2:
     a graph titled "Solution concentration ..." is input).
  2. *Text by containment.* Every own text block that remains must lie
     inside the statement: its whole text, less at most a leading label or
     heading ("Exercise 6.", "(a)": :func:`_is_label`), is a run of the
     statement's words (compared without spaces, so "3 + 3" places "3+3").
     A block that is only a label prints too. Words after the statement in
     a block, other words before it, or a block the statement does not
     place mean doubt.
  3. *Coverage from what prints.* The printed text blocks must print the
     whole statement between them; a dropped block supplies nothing (F3: a
     part (b) inside a solution block never leaves part (a) printed alone).

  Any doubt gives no free crop at all (``NO_CROP``: "the crop isn't
  available for this problem · the original page is"), and the original
  page, one hint before Submit, is still offered. A guard that cannot be
  read fails closed the same way. No answer-leak test is needed: a block
  inside the statement shows nothing the prompt does not.
* **Figures by role, not by words.** An import since the redesign records
  each selected figure's role for the item, from the import author's
  structured output (``exercise_authoring._figure_roles``: ``stimulus``,
  ``answer``, ``worked``, ``unrelated``, validated), and owns a figure only
  as a validated stimulus. An import before it recorded no role and owns
  figures by its old marks (a single-exercise import: every block selected).
  One rule reads both, so an old mark is never trusted further than this:
  a solution block (rule 1) is never the problem's figure; in the free crop
  an owned figure shows only when it comes before every solution block and
  every text block a solution or proof heading runs into, in reading order (any
  other is left to the original page beside it); and it is kept to the
  learner's selected sub-box. A check on your own cannot open the page, so
  there an owned figure shows unless it is a solution block (the problem
  must stay answerable). The residual, an unmarked completed answer figure
  owned by an old mark, is an owner question
  (``docs/reviews/astra-batch1-fixes.md``, Redesign).
* **The cold rule** (D46, spec G61). During a check on your own (a due
  "Check once", a cold follow-up, an active diagnostic presentation; the
  caller reads which, F1) the view
  carries no locator, page, label, link, photo or crop, except the
  figure-only exception (§15 Q10): a figure the problem uses as input is
  part of its stimulus, so it is cropped to the figure alone, with no
  caption, number, page or box, whether or not the text gives a free crop.
* **A variant is not the book's problem.** An item varied from a textbook
  exercise (``relation = "variant_of"``) has no print of its own: none is
  shown (the parent's print would be another problem, and its neighbours).
* **No exposure, no model call.** The crop is the stem the learner already
  has, so nothing is recorded; the original page records its exposure where
  it opens (``get_span_view``), as every source opening does.

``practice.as_printed.enabled`` off: no view (every screen as before CA1).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

from learnloop.ingest.ir import DocumentBlock, is_figure_block, page_region, selection_region

#: Reads blocks' effective roles over a connection, keyed (extraction, span)
#: (``source_retrieval.corpus.block_roles``: a solution region's body
#: included). Passed in by the caller: the Reader sits below source retrieval.
RoleReader = Callable[[Any, Sequence[tuple[str, str]]], Mapping[tuple[str, str], str | None]]

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
    """One crop: one retained region (a block's box, or its selected sub-box) on one page."""

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


def _overlap(a: Box, b: Box) -> Box | None:
    left, top = max(a[0], b[0]), max(a[1], b[1])
    right, bottom = min(a[2], b[2]), min(a[3], b[3])
    return (left, top, right, bottom) if right > left and bottom > top else None


def crop_boxes(
    own: Sequence[DocumentBlock],
    regions: Mapping[str, tuple[int, Box]] | None = None,
) -> tuple[list[CropBox], list[str]]:
    """The crops of ``own`` (the problem's blocks), one per block in reading
    order, and the span ids that crop nothing (no page or no box).
    ``regions``: a learner-drawn sub-box per span (page, box), used in place
    of that block's box, clipped to it (RW5a's rule; a region on another
    page is ignored, one outside the block crops nothing).

    Never merged (the Astra redesign, F6): a crop is exactly one retained
    region, so it can hold no pixel of a block or sub-box left out (a
    rectangle joining two regions could)."""

    crops: list[CropBox] = []
    skipped: list[str] = []
    for block in sorted(own, key=lambda candidate: candidate.ordinal):
        box = _box(block)
        if block.page is None or box is None:
            skipped.append(block.span_id)
            continue
        page = int(block.page)
        region = (regions or {}).get(block.span_id)
        if region is not None and int(region[0]) == page:
            box = _overlap(region[1], box)
            if box is None:
                skipped.append(block.span_id)
                continue
        crops.append(CropBox(page, box, (block.span_id,)))
    return crops, skipped


def _outside(outer: Box, inner: Box) -> list[Box]:
    """``outer`` less ``inner`` (inside it), as at most four rectangles."""

    left, top, right, bottom = outer
    il, it, ir, ib = inner
    parts = [(left, top, right, it), (left, ib, right, bottom), (left, it, il, ib), (ir, it, right, ib)]
    return [part for part in parts if part[2] > part[0] and part[3] > part[1]]


#: An excluded area, and whether it is a block's whole box (which may be a
#: container around a retained block: :func:`_masks_for`).
Excluded = tuple[Box, bool]


def excluded_areas(
    retained: Sequence[DocumentBlock],
    on_pages: Sequence[DocumentBlock],
    regions: Mapping[str, tuple[int, Box]] | None = None,
) -> dict[int, list[Excluded]]:
    """Per page, the areas no crop may show (Sol verify 3): the box of every
    block on the page that is not ``retained``, and for a retained block
    shown by its selected sub-box (``regions``), the rest of its box. The
    renderer paints them white in each crop (:func:`_masks_for`)."""

    retained_ids = {block.span_id for block in retained}
    areas: dict[int, list[Excluded]] = {}
    for block in on_pages:
        box = _box(block)
        if block.page is not None and box is not None and block.span_id not in retained_ids:
            areas.setdefault(int(block.page), []).append((box, True))
    for block in retained:
        box, region = _box(block), (regions or {}).get(block.span_id)
        if block.page is None or box is None or region is None or int(region[0]) != int(block.page):
            continue
        shown = _overlap(region[1], box)
        rest = _outside(box, shown) if shown is not None else [box]
        areas.setdefault(int(block.page), []).extend((part, False) for part in rest)
    return areas


def _contains(outer: Box, inner: Box) -> bool:
    return outer[0] <= inner[0] and outer[1] <= inner[1] and inner[2] <= outer[2] and inner[3] <= outer[3]


def _masks_for(crop: Box, areas: Sequence[Excluded]) -> list[list[float]]:
    """The excluded areas one crop paints white: those overlapping it, except
    a block's box holding the whole crop. That is a container the extractor
    drew around the retained block (a figure group around its figure); its
    other members are blocks of their own, masked by their own boxes, and
    painting it would blank the retained block (a required graph lost cold).
    The rest of a sub-box's block is always painted."""

    return [list(part) for area, block_box in areas if not (block_box and _contains(area, crop))
            for part in [_overlap(area, crop)] if part is not None]


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
    #: ``span_ids`` (the crop's own blocks): a selection import names every
    #: block it was imported from here, and only this item's own in
    #: ``span_ids`` (empty when that can't be read: no free crop, the charged
    #: page only; Codex re-review F9). None: ``span_ids``.
    page_span_ids: tuple[str, ...] | None = None
    #: The figures a check on your own shows (§15 Q10), set by
    #: :func:`_problem_only`; None: the figures among ``span_ids``.
    figure_span_ids: tuple[str, ...] | None = None

    @property
    def located_by(self) -> tuple[str, ...]:
        return self.span_ids if self.page_span_ids is None else self.page_span_ids

    @property
    def stimulus(self) -> tuple[str, ...]:
        """The blocks a check on your own may crop figures from."""

        return self.span_ids if self.figure_span_ids is None else self.figure_span_ids


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


def _block_refs(item: Any) -> list[tuple[str, str, Any]]:
    """The item's ``block_span_v1`` source refs: (extraction, span, ref)."""

    from learnloop.ingest.locators import parse_block_span

    found: list[tuple[str, str, Any]] = []
    for ref in getattr(getattr(item, "provenance", None), "source_refs", None) or []:
        if _ref_field(ref, "ref_type") != "canonical_source":
            continue
        parsed = parse_block_span(str(_ref_field(ref, "locator") or ""))
        if parsed is not None:
            found.append((parsed[0], parsed[1], ref))
    return found


def _selection_origin(repository: Any, item: Any) -> PrintedOrigin | None:
    """A Reader selection import (``reader.import_exercise``, the workbench's
    "work through this"): marked by its ``learner_item_authored`` event (the
    origin alone is shared with AI proposals over sources), its blocks named
    by its ``block_span_v1`` source refs, else by its import rows."""

    from learnloop.db.stores.source_service import imports_for_item, is_reader_import

    provenance = getattr(item, "provenance", None)
    if getattr(provenance, "origin", None) != "canonical_extract":
        return None
    with repository.connection() as connection:
        if not is_reader_import(connection, item.id):
            return None
        rows = [row for row in imports_for_item(connection, item.id) if row.get("caller") == "reader"]
    extraction_id: str | None = None
    spans: list[str] = []
    #: Re-review F9: ``owned`` per block (absent: written before ownership was kept).
    ownership: dict[str, bool] = {}
    regions: dict[str, tuple[int, Box]] = {}
    source_id: str | None = None
    for ref_extraction, span, ref in _block_refs(item):
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
    # Final verify F9: a free crop needs evidence that its blocks are this
    # item's alone. The import records it per block (``owned``; a figure's is
    # its validated stimulus role, the Astra redesign); a Reader import
    # without it was written before that, and nothing durable says whether
    # the selection also held other exercises. Unknown is not unsplit: no
    # free crop, the original page (charged before Submit) still offered.
    own = tuple(span for span in spans if ownership.get(span, False))
    return PrintedOrigin(extraction_id=extraction_id, span_ids=own, source_id=source_id,
                         regions={span: box for span, box in regions.items() if span in own},
                         page_span_ids=tuple(spans))


def _canonical_origin(item: Any) -> PrintedOrigin:
    """A ``canonical_exercise``: the sources service's exercise region names
    its blocks. A figure among them whose ref records a role the import
    validated as not stimulus (the Astra redesign: ``owned`` false beside a
    ``figure_role``) is not the problem's."""

    canonical = item.canonical_exercise
    refused = {span for extraction, span, ref in _block_refs(item)
               if extraction == canonical.extraction_id and _ref_field(ref, "figure_role") is not None
               and _ref_field(ref, "owned") is not True}
    spans = tuple(str(span) for span in canonical.span_ids)
    return PrintedOrigin(extraction_id=canonical.extraction_id, span_ids=tuple(span for span in spans if span not in refused),
                         source_id=canonical.source_id, label=canonical.label, relation=canonical.relation,
                         page_span_ids=spans)


#: A solution or proof heading that starts a text block or a part of one:
#: the word alone, or with a number or enumerator, then punctuation or the
#: end of the line ("Solution", "Solution.", "Solution 3.2:", "Proof.",
#: "Solutions (a) -"). Sol verify 2: never a word starting a sentence
#: ("Solution concentration (mol/L) versus time (s)." is a graph's title),
#: and never read on a figure's text: a figure leaves only by its solution
#: span, its solution role or its validated figure role.
_ANSWER_HEADING = re.compile(
    r"\s*(?P<kind>solutions?|proofs?)(?:\s+(?:\d+(?:[.\-]\d+)*[a-z]?|\(?[a-z]\)|\(?[ivxlc]+\)))?"
    r"\s*(?:[.:;\u2013\u2014-]|$)",
    re.IGNORECASE,
)
#: Where a block's text is cut to read the lead of each part: a line break,
#: or the space after a sentence or clause ends.
_PART_BREAK = re.compile(r"\n+|(?<=[.!?:;)])\s+")


def _tokens(text: str | None) -> list[str]:
    return str(text or "").split()


def _joined(tokens: list[str]) -> tuple[str, list[int]]:
    """The words run together without spaces, and where each word starts in
    that run (with its end): word boundaries, where a placement may begin or
    end."""

    offsets = [0]
    for token in tokens:
        offsets.append(offsets[-1] + len(token))
    return "".join(tokens), offsets


def _words(tokens: list[str], offsets: list[int], start: int, end: int) -> str:
    """The words between two boundaries of :func:`_joined`."""

    return " ".join(tokens[offsets.index(start):offsets.index(end)])


def _occurrences(haystack: str, needle: str) -> list[int]:
    found, at = [], haystack.find(needle)
    while at >= 0:
        found.append(at)
        at = haystack.find(needle, at + 1)
    return found


@dataclass(frozen=True)
class _Placement:
    """Where the statement places a block: the block's words before and
    after the statement's text in it, and the part of the statement it
    prints (``start``, ``end``: positions in the statement's words run
    together without spaces)."""

    before: str
    after: str
    start: int
    end: int


def _placement(block_text: str, statement: str) -> _Placement | None:
    """Where the statement places a block, or None when nothing does (they
    share no run of words: the block is not the statement's, or the learner
    reworded it). The block may sit inside the statement, the statement
    inside the block, or the two overlap at an edge (a statement over several
    blocks). Compared as the same characters without spaces (Codex re-review
    of the Astra fixes, F3: a learner's edit that only moved spaces, "3 + 3"
    for "3+3", places the block, its edges too), each match starting and
    ending where a word does in both texts (no match inside a word: a lone
    "4" does not place itself in "24")."""

    block, stem = _tokens(block_text), _tokens(statement)
    if not block or not stem:
        return None
    joined_block, block_at = _joined(block)
    joined_stem, stem_at = _joined(stem)
    block_edges, stem_edges = set(block_at), set(stem_at)
    for at in _occurrences(joined_stem, joined_block):
        if at in stem_edges and at + len(joined_block) in stem_edges:
            return _Placement("", "", at, at + len(joined_block))
    for at in _occurrences(joined_block, joined_stem):
        if at in block_edges and at + len(joined_stem) in block_edges:
            return _Placement(_words(block, block_at, 0, at),
                              _words(block, block_at, at + len(joined_stem), len(joined_block)),
                              0, len(joined_stem))
    sizes = sorted({edge for edge in stem_edges} | {len(joined_stem) - edge for edge in stem_edges}, reverse=True)
    for size in sizes:
        if not 0 < size < min(len(joined_block), len(joined_stem)) + 1:
            continue
        cut = len(joined_block) - size
        if (cut in block_edges and size in stem_edges and cut > 0
                and joined_block[cut:] == joined_stem[:size]):
            return _Placement(_words(block, block_at, 0, cut), "", 0, size)
        rest = len(joined_stem) - size
        if (size in block_edges and rest in stem_edges and size < len(joined_block)
                and joined_block[:size] == joined_stem[rest:]):
            return _Placement("", _words(block, block_at, size, len(joined_block)), rest, len(joined_stem))
    return None


def _covers(parts: Sequence[_Placement], statement: str) -> bool:
    """Whether the placed parts print the whole statement between them
    (Codex re-review F3: never a partial print)."""

    length = len(_joined(_tokens(statement))[0])
    reach = 0
    for part in sorted(parts, key=lambda placed: placed.start):
        if part.start > reach:
            return False
        reach = max(reach, part.end)
    return length > 0 and reach >= length


#: Words a label or heading before an exercise's statement may hold ("Exercise
#: 6.", "Problem 3.2:", "Q3.", "Exercises"): its kind, never another sentence.
_LABEL_WORDS = r"exercises?|problems?|questions?|parts?|tasks?|examples?|ex|prob|no|q"
#: Kinds that are a label only with a number ("No." alone is an answer).
_NUMBERED_ONLY = frozenset({"ex", "prob", "no", "q"})
_LABEL_TOKEN = re.compile(
    rf"(?P<marks>[§#*†‡★☆]*)(?P<kind>{_LABEL_WORDS})?\.?(?P<open>[(\[])?"
    r"(?P<enum>\d+(?:[.\-]\d+)*[a-z]?|[a-z]|[ivxlcdm]+)?(?P<close>[)\]])?(?P<end>[.:]*)",
    re.IGNORECASE,
)
_ROMAN = re.compile(r"m{0,3}(?:cm|cd|d?c{0,3})(?:xc|xl|l?x{0,3})(?:ix|iv|v?i{0,3})", re.IGNORECASE)
_DASHES = frozenset({"-", "\u2013", "\u2014", ":"})


def _label_token(token: str) -> str | None:
    """``"label"`` for a word a label may hold, ``"kind"`` for a kind that
    is one only with a number after it ("No.", "Q."), ``"number"`` for a
    number, else None."""

    if token in _DASHES:
        return "label"
    match = _LABEL_TOKEN.fullmatch(token)
    if match is None:
        return None
    kind, enum = (match.group("kind") or "").lower(), match.group("enum")
    if not kind and not enum:
        return "label" if match.group("marks") and not match.group("open") and not match.group("close") else None
    if match.group("open") and not match.group("close"):
        return None
    if kind in _NUMBERED_ONLY and not enum:
        return "kind"
    if enum and not kind and not enum[0].isdigit():
        # A letter or a roman numeral is an enumerator only as one: "(a)",
        # "b)", "iv." (a bare "a" or "mix" is a word).
        if not (match.group("close") or match.group("end")):
            return None
        if len(enum) > 1 and not _ROMAN.fullmatch(enum):
            return None
    return "number" if enum and not kind and enum[0].isdigit() else "label"


def _is_label(text: str) -> bool:
    """Whether words before a statement in its block are affirmatively a
    label or heading (Codex re-review of the Astra fixes, F1): an exercise's
    kind and number, an enumerator, a section mark, nothing else. "The answer
    is 4." is not, whatever a leak test says."""

    kinds = [_label_token(token) for token in _tokens(text)]
    if not kinds or None in kinds:
        return False
    return all(kind != "kind" or (index + 1 < len(kinds) and kinds[index + 1] == "number")
               for index, kind in enumerate(kinds))


def _contained(block_text: str, statement: str) -> tuple[bool, _Placement | None]:
    """Whether a text block lies inside the statement (rule 2 of the module
    docstring), and the part of the statement it prints. It does when the
    statement places it with no words after the statement in the block and,
    before it, none or only a label or heading (:func:`_is_label`; Codex
    re-review F1: "The answer is 4." is not one), or when the whole block is
    a label (it prints no part of the statement). Anything else is doubt."""

    placed = _placement(block_text, statement)
    if placed is not None and not placed.after and (not placed.before or _is_label(placed.before)):
        return True, placed
    return (True, None) if _is_label(block_text) else (False, None)


def _answer_heading(text: str | None) -> str | None:
    """``"solution"`` or ``"proof"`` when a heading of that kind starts the
    text's first line (:data:`_ANSWER_HEADING`), else None."""

    lines = str(text or "").strip().splitlines()
    match = _ANSWER_HEADING.match(lines[0]) if lines else None
    return None if match is None else ("proof" if match.group("kind").lower().startswith("proof") else "solution")


def _runs_into_solution(text: str | None) -> bool:
    """Whether a solution or proof heading starts any part of a block's text."""

    return any(_answer_heading(part) for part in _PART_BREAK.split(str(text or "")) if part.strip())


def _solution_span_ids(connection: Any, item_id: str, extraction_id: str) -> set[str]:
    """The book-solution blocks the item's import checks found (each import
    row's ``verification``: ``book_solution``, ``solution_search``)."""

    from learnloop.db.stores.source_service import imports_for_item

    found: set[str] = set()
    for row in imports_for_item(connection, item_id):
        verification = row.get("verification") or {}
        for key in ("book_solution", "solution_search"):
            entry = verification.get(key) or {}
            if not isinstance(entry, Mapping) or entry.get("extraction_id") not in (None, extraction_id):
                continue
            found.update(str(span) for span in entry.get("span_ids") or () if span)
    return found


def _problem_only(repository: Any, item: Any, origin: PrintedOrigin, *,
                  roles: RoleReader | None = None) -> PrintedOrigin:
    """The origin narrowed to the problem (module docstring, "Only the
    problem, never the solution" and "Figures by role"): ``span_ids`` the
    free crop (empty: ``NO_CROP``), ``figure_span_ids`` the figures a check
    on your own shows, ``page_span_ids`` the original page's outline, none
    of them a solution block. ``roles`` reads the blocks' effective roles
    (else each block's stored hint). Fails closed: a guard that cannot be
    read leaves no free crop and no figure, the original page still offered."""

    if not origin.span_ids:
        return origin
    no_crop = replace(origin, span_ids=(), regions={}, page_span_ids=origin.located_by, figure_span_ids=())
    wanted = list(dict.fromkeys((*origin.located_by, *origin.span_ids)))
    try:
        blocks = {block.span_id: block for block in repository.document_blocks(origin.extraction_id, wanted)}
        with repository.connection() as connection:
            solution = _solution_span_ids(connection, str(getattr(item, "id", "")), origin.extraction_id)
            role_of = (dict(roles(connection, [(origin.extraction_id, span) for span in blocks])) if roles is not None
                       else {(origin.extraction_id, span): block.role_hint for span, block in blocks.items()})
    except Exception:  # noqa: BLE001 - fail closed: no free crop, the page still offered
        import logging

        logging.getLogger(__name__).exception("Could not read the solution blocks of %s", getattr(item, "id", "?"))
        return no_crop

    # Rule 1: solution blocks leave, whatever the marks say. The heading test
    # reads text blocks only (Sol verify 2: a graph titled "Solution
    # concentration ..." is the problem's input).
    dropped = {span for span, block in blocks.items()
               if span in solution or role_of.get((origin.extraction_id, span)) == "solution"
               or (not is_figure_block(block) and _answer_heading(block.text) == "solution")}
    located = tuple(span for span in origin.located_by if span not in dropped) or origin.located_by
    own = [span for span in origin.span_ids if span in blocks and span not in dropped]
    figures = [span for span in own if is_figure_block(blocks[span])]
    text = [span for span in own if span not in figures]
    # In the free crop, an owned figure before every solution start in
    # reading order (an old mark may own a completed answer figure; the
    # original page beside the crop shows the rest).
    first_solution = min((block.ordinal for span, block in blocks.items()
                          if span in dropped or (not is_figure_block(block) and _runs_into_solution(block.text))),
                         default=None)
    free_figures = {span for span in figures if first_solution is None or blocks[span].ordinal < first_solution}

    def kept_regions(spans: Sequence[str]) -> dict[str, tuple[int, Box]]:
        # Codex re-review F6: a kept block keeps the learner's sub-box, crop or no crop.
        return {span: box for span, box in origin.regions.items() if span in spans}

    # Rules 2 and 3: every own text block inside the statement, and the
    # blocks that print (never a dropped one, F3; a printed figure whose text
    # the statement quotes counts) print all of it.
    statement = str(getattr(item, "prompt", "") or "")
    placed = [_contained(blocks[span].text, statement) for span in text]
    printed = [part for _inside, part in (*placed, *(_contained(blocks[span].text, statement)
                                                     for span in free_figures)) if part is not None]
    if not text or not all(inside for inside, _part in placed) or not _covers(printed, statement):
        return replace(no_crop, page_span_ids=located, figure_span_ids=tuple(figures),
                       regions=kept_regions(figures))
    shown = tuple(span for span in own if span in text or span in free_figures)
    return replace(origin, span_ids=shown, regions=kept_regions((*shown, *figures)), page_span_ids=located,
                   figure_span_ids=tuple(figures))


def printed_origin(repository: Any, item: Any, *, roles: RoleReader | None = None) -> PrintedOrigin | None:
    """The item's print, or None (pasted text, a generated card, a photo card).
    Narrowed to the problem (:func:`_problem_only`, ``roles`` as there: the
    desktop RPC passes source retrieval's role reader)."""

    if getattr(item, "canonical_exercise", None) is not None:
        origin: PrintedOrigin | None = _canonical_origin(item)
    elif repository is None:
        return None
    else:
        try:
            origin = _selection_origin(repository, item)
        except Exception:  # noqa: BLE001 - an unreadable origin shows no print, never an error
            import logging

            logging.getLogger(__name__).exception("Could not read where %s was imported from",
                                                  getattr(item, "id", "?"))
            return None
    if origin is None or repository is None:
        return origin
    return _problem_only(repository, item, origin, roles=roles)


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
    boxes, skipped = crop_boxes(blocks, regions)
    pages = sorted({box.page for box in boxes})
    neighbours = repository.document_blocks_on_pages(extraction_id, pages) if pages else []
    masks = excluded_areas(blocks, neighbours, regions)
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
            made, _size = SV._local_pdf_crops(pdf_path, page, [list(boxes[i].bbox) for i in indices],
                                              masks=[_masks_for(boxes[i].bbox, masks.get(page, []))
                                                     for i in indices])
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


def _label(label: str | None) -> str | None:
    """CA1 polish: an exercise label with no text is no label (the header
    then names the book and page only, no empty part)."""

    text = (label or "").strip()
    return text or None


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
        "locator": {"source_title": source_title, "exercise_label": _label(origin.label), "page_label": label_text},
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
    roles: RoleReader | None = None,
) -> dict[str, Any]:
    """The practice view of ``item`` as printed (K15). ``cold``: a check on
    your own now (the caller reads it on the server, D46); ``photo``: the
    capture the card was written from, when there is one; ``origin``: where
    its print is (read here when not given, :func:`printed_origin` with
    ``roles``)."""

    if not enabled:
        return {"enabled": False, "kind": KIND_NONE, "cold": cold, "reason": "disabled"}
    if origin is None:
        origin = printed_origin(repository, item, roles=roles)
    if origin is not None:
        if origin.relation != "verbatim":
            return _none("variant", cold=cold)
        if cold:
            # Codex review F2: the problem's figures (:func:`_problem_only`),
            # whether or not the text gives a free crop (the problem needs its
            # input figure to be answered; the page cannot open now).
            figures = (printed_crops(repository, extraction_id=origin.extraction_id, span_ids=origin.stimulus,
                                     render=render, figure_only=True, regions=origin.regions)
                       if origin.stimulus else {"crops": []})
            if not figures["crops"]:
                return _none("cold_check", cold=True)
            return {"enabled": True, "kind": KIND_FIGURE, "cold": True, "label": FIGURE_LABEL,
                    "status": figures["status"], "crops": figures["crops"]}
        if not origin.span_ids:
            return _page_without_crop(repository, origin, source_title=source_title, cold=cold)
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
            "locator": {"source_title": source_title, "exercise_label": _label(origin.label),
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
