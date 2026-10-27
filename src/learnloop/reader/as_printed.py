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
  block's own box. A selection the import split into several exercises
  marks on each ref whether that block is this item's own (``owned``), and
  only those are cropped; where that is not known (a selection-level edit,
  or a split written before the mark) no crop is free, and the original
  page (one hint before Submit) is still offered (Codex re-review F9).
* **Never the solution** (Astra batch review; owner 2026-10-26: "i would
  hope that crop excludes the solution"). Whatever the stored marks say (an
  import before this rule marked every block it was given), a block on the
  item's book-solution spans (its import's check found them) or with a
  solution role (its effective role, or a "Solution" lead) is never cropped.
  The crop is free only when every own text block is affirmatively the stem
  (Codex review of the Astra fixes, F1): the statement places it and its
  other words all come before the statement and are a label or heading
  ("Exercise 6.", "(a)"; re-review F1: "The answer is 4." is not, whatever a
  leak test says), and its blocks print the whole statement between them
  (re-review F3). Words after the statement in its block, other words
  before it, a block the statement does not place, a solution or proof lead
  inside it, words beside it that give the expected answer away, a solution
  block that also holds statement words (F3; compared without spaces, so a
  learner's "3 + 3" for the printed "3+3" still places it), or a part of the
  statement no kept block prints leave no free crop at all (``NO_CROP``:
  never a partial print); the original page, one hint before Submit, is
  still offered. A guard that cannot be read fails closed the same way.
* **A selection's figures** (Codex re-review F5). A figure selected with a
  problem is its own (cropped, or its stimulus) only when the statement
  refers to it (names its number, or points at the one figure selected:
  "the line shown") or echoes text of it no text block prints; selected is
  not enough (a completed answer graph selected with "Sketch y=x^2." is the
  answer). A kept figure keeps the learner's drawn sub-box whether or not
  the text gives a free crop (re-review F6).
* **The cold rule** (D46, spec G61). During a check on your own (a due
  "Check once", a cold follow-up, an active diagnostic presentation; the
  caller reads which, F1) the view
  carries no locator, page, label, link, photo or crop, except the
  figure-only exception (§15 Q10): a figure block the problem was imported
  with is part of its stimulus, so it is cropped to the figure alone, with
  no caption, number, page or box; kept whether or not the statement echoes
  the figure's text and when the text gives no free crop (F2), when the
  statement refers to it (F5), and to the learner's sub-box (F6).
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
from fractions import Fraction
from typing import Any

from learnloop.ingest.block_roles import lead_role, referenced_figures
from learnloop.ingest.ir import DocumentBlock, is_figure_block, page_region, selection_region

#: Reads blocks' effective roles over a connection, keyed (extraction, span)
#: (``source_retrieval.corpus.block_roles``: a solution region's body
#: included). Passed in by the caller: the Reader sits below source retrieval.
RoleReader = Callable[[Any, Sequence[tuple[str, str]]], Mapping[tuple[str, str], str | None]]
#: Whether a text gives an expected answer away (``tutor_qa.span_leaks_expected``).
LeakCheck = Callable[[str, Any], bool]

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
    #: Codex review of the Astra fixes, F2: the figures the problem was
    #: imported with (its stimulus), kept for a check on your own (§15 Q10)
    #: even when its text gives no free crop or the statement does not echo
    #: the figure. None: the figures among ``span_ids``.
    figure_span_ids: tuple[str, ...] | None = None
    #: Codex re-review F5: a selection's figures are the problem's only when
    #: its statement refers to them (``ingest.block_roles.referenced_figures``)
    #: or echoes text of them no text block prints; selected is not enough.
    #: False for a ``canonical_exercise`` (the sources service's exercise
    #: region decided its blocks).
    figures_need_reference: bool = False

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
    #: Re-review F9: ``owned`` per block (absent: written before ownership was kept).
    ownership: dict[str, bool] = {}
    #: Codex review F2: the figures a single-exercise import keeps as its stimulus.
    stimulus: set[str] = set()
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
        if _ref_field(ref, "stimulus") is True:
            stimulus.add(span)
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
    # item's alone. The import records it per block (``owned``); a Reader
    # import without it was written before that, and nothing durable says
    # whether the selection also held other exercises (a split's skipped or
    # deduplicated sibling leaves no item and no row; an import made with
    # source_service off leaves no row at all). Unknown is not unsplit: no
    # free crop, the original page (charged before Submit) still offered.
    own = tuple(span for span in spans if ownership.get(span, False))
    figures = tuple(span for span in spans if span in own or span in stimulus)
    # Codex re-review F6: a stimulus figure keeps the learner's sub-box too.
    return PrintedOrigin(extraction_id=extraction_id, span_ids=own, source_id=source_id,
                         regions={span: box for span, box in regions.items() if span in own or span in figures},
                         page_span_ids=tuple(spans), figure_span_ids=figures, figures_need_reference=True)


#: The leads that start a worked answer inside a block that began as the
#: stem ("... Solution: x = 2", "Prove that ... Proof. ..."): such a block
#: holds the stem and its solution together.
_ANSWER_LEADS = frozenset({"solution", "proof"})
#: Where a block's text is cut to read the lead of each part: a line break,
#: or the space after a sentence or clause ends.
_PART_BREAK = re.compile(r"\n+|(?<=[.!?:;)])\s+")


def _tokens(text: str | None) -> list[str]:
    return str(text or "").split()


def _find(tokens: list[str], part: list[str]) -> int:
    """Where ``part`` sits in ``tokens`` as a run of whole words, or -1."""

    width = len(part)
    for start in range(len(tokens) - width + 1):
        if tokens[start:start + width] == part:
            return start
    return -1


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


def _stem_only(block_text: str, statement: str, expected_answer: Any, leaks: LeakCheck | None = None) -> bool:
    """Whether a block of the problem is affirmatively its stem only, so it
    may be cropped for free (Codex review of the Astra fixes, F1: a leak test
    that finds nothing does not make a block safe; its matcher ignores a lone
    digit or a short word). It is when the statement places it (inside the
    statement, or the statement inside it) and its only other words come
    before the statement and are a label or heading (:func:`_is_label`; Codex
    re-review F1). Not when words follow the statement in the block (an
    answer, a solution, a hint, the next exercise), when words before it are
    anything but a label, when nothing places it, when a solution or proof
    lead starts a later part of it, or when (with ``leaks``, the tutor's leak
    matcher ``tutor_qa.span_leaks_expected``) its label gives the expected
    answer away while the statement does not."""

    parts = [part for part in _PART_BREAK.split(str(block_text or "")) if part.strip()]
    if any(lead_role(part) in _ANSWER_LEADS for part in parts[1:]):
        return False
    placed = _placement(block_text, statement)
    if placed is None or placed.after:
        return False
    if not placed.before:
        return True
    if not _is_label(placed.before):
        return False
    if leaks is None or expected_answer in (None, "", {}):
        return True
    return not (leaks(placed.before, expected_answer) and not leaks(statement, expected_answer))


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


def _without_solutions(repository: Any, item: Any, origin: PrintedOrigin, *, roles: RoleReader | None = None,
                       leaks: LeakCheck | None = None) -> PrintedOrigin:
    """The origin with no solution in its free crop (module docstring, "Never
    the solution"): solution blocks leave the crop's own blocks, its figures
    and the original page's outline; the crop is free only when every own
    text block is affirmatively stem only (:func:`_stem_only`), else no free
    crop. ``roles`` reads the blocks' effective roles (else each block's
    stored hint); ``leaks`` the answer-leak matcher (else no leak test).
    Fails closed: a guard that cannot be read leaves no free crop and no
    figure, the original page still offered."""

    if not origin.span_ids and not origin.stimulus:
        return origin

    def kept_regions(spans: Sequence[str]) -> dict[str, tuple[int, Box]]:
        # Codex re-review F6: a kept figure keeps the learner's sub-box, crop or no crop.
        return {span: box for span, box in origin.regions.items() if span in spans}

    no_crop = replace(origin, span_ids=(), regions={}, page_span_ids=origin.located_by, figure_span_ids=())
    wanted = list(dict.fromkeys((*origin.located_by, *origin.stimulus)))
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

    statement = str(getattr(item, "prompt", "") or "")
    expected = getattr(item, "expected_answer", None)
    placed = {span: _placement(block.text, statement) for span, block in blocks.items()}

    def solution_kind(span: str) -> str | None:
        """``"solution"``: a block of the book's solution (on its spans, or
        led by "Solution", sharing no words with the statement or wholly
        inside it; a block in a solution region the statement does not
        share). ``"unsure"``: a solution block that also holds words the
        statement places beside its own (Codex review F3: part of the
        problem with its answer; dropping it would print the problem in
        part), or a solution region's block the statement shares words with
        (an exercise printed straight after the previous one's solution
        reads as its body). None: not a solution."""

        block = blocks.get(span)
        here = placed.get(span)
        if span in solution or (block is not None and lead_role(block.text) == "solution"):
            return "solution" if here is None or (not here.before and not here.after) else "unsure"
        if role_of.get((origin.extraction_id, span)) != "solution":
            return None
        return "unsure" if here is not None else "solution"

    def is_figure(span: str) -> bool:
        return span in blocks and is_figure_block(blocks[span])

    kinds = {span: solution_kind(span) for span in wanted}
    dropped = {span for span, kind in kinds.items() if kind == "solution"}
    own = [span for span in origin.span_ids if span not in dropped]
    figures = [span for span in origin.stimulus if span not in dropped]
    if origin.figures_need_reference:
        # Codex re-review F5: selected is not enough. A figure stays the
        # problem's when the statement refers to it, or echoes text of it
        # that no text block of the problem prints.
        text_parts = [placed[span] for span in own if not is_figure(span) and placed.get(span) is not None]
        selected = [(span, blocks[span].text) for span in origin.located_by if is_figure(span) and span not in dropped]
        referenced = referenced_figures(statement, selected)

        def echoed(span: str) -> bool:
            here = placed.get(span)
            return here is not None and not any(part.start <= here.start and here.end <= part.end
                                                for part in text_parts)

        figures = [span for span in figures if not is_figure(span) or span in referenced or echoed(span)]
        own = [span for span in own if not is_figure(span) or span in figures]
    located = tuple(span for span in origin.located_by if span not in dropped) or origin.located_by
    withheld = replace(no_crop, page_span_ids=located, figure_span_ids=tuple(figures),
                       regions=kept_regions(figures))
    text_own = [span for span in own if span in blocks and not is_figure(span)]
    # Codex re-review F3: the crop must print the whole statement. The parts
    # its kept blocks print, with the parts a dropped solution block wholly
    # inside the statement held (the learner's own prompt took the book's
    # solution in), must leave nothing of the statement out.
    printed = [placed[span] for span in own if placed.get(span) is not None]
    printed += [placed[span] for span in dropped
                if placed.get(span) is not None and not placed[span].before and not placed[span].after]
    if (not own or any(kinds.get(span) == "unsure" for span in own)
            or not all(_stem_only(blocks[span].text, statement, expected, leaks) for span in text_own)
            or not _covers(printed, statement)):
        return withheld
    return replace(origin, span_ids=tuple(own), regions=kept_regions((*own, *figures)),
                   page_span_ids=located, figure_span_ids=tuple(figures))


def printed_origin(repository: Any, item: Any, *, roles: RoleReader | None = None,
                   leaks: LeakCheck | None = None) -> PrintedOrigin | None:
    """The item's print, or None (pasted text, a generated card, a photo card).
    Its own blocks never include a solution (:func:`_without_solutions`;
    ``roles`` and ``leaks`` as there: the desktop RPC passes source
    retrieval's role reader and the tutor's leak matcher)."""

    canonical = getattr(item, "canonical_exercise", None)
    if canonical is not None:
        origin: PrintedOrigin | None = PrintedOrigin(
            extraction_id=canonical.extraction_id, span_ids=tuple(canonical.span_ids),
            source_id=canonical.source_id, label=canonical.label, relation=canonical.relation)
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
    return _without_solutions(repository, item, origin, roles=roles, leaks=leaks)


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
    leaks: LeakCheck | None = None,
) -> dict[str, Any]:
    """The practice view of ``item`` as printed (K15). ``cold``: a check on
    your own now (the caller reads it on the server, D46); ``photo``: the
    capture the card was written from, when there is one; ``origin``: where
    its print is (read here when not given, :func:`printed_origin` with
    ``roles`` and ``leaks``)."""

    if not enabled:
        return {"enabled": False, "kind": KIND_NONE, "cold": cold, "reason": "disabled"}
    if origin is None:
        origin = printed_origin(repository, item, roles=roles, leaks=leaks)
    if origin is not None:
        if origin.relation != "verbatim":
            return _none("variant", cold=cold)
        if cold:
            # Codex review F2: the stimulus figures, whether or not the text
            # gives a free crop (the problem needs its figure to be answered).
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
