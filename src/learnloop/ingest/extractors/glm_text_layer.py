"""A PDF's own text layer, for what GLM-OCR's answers never carry.

The hosted layout service never returns footnote, page-header, page-footer,
page-number or equation-number regions (39 of 39 live answers, 2026-10-14;
docs/reviews/glm-ocr-quality.md). A born-digital PDF still has them in its
text layer. pdfium's text runs, placed in the Reader's coordinates (PDF
points, top-left origin, the crop box after rotation, the same space as the
block boxes), give back:

- footnotes: lines below every region of their column, near the page's foot,
  set off from the region above and starting at its left edge, that no
  region read, that are not page numbers or running lines (short lines in
  the top or bottom margin, at the same height on several of the pages
  read), and whose text is not already in the page's blocks;
- display-equation numbers: one "(n)" beside a display region, in its band
  and inside no other region, becomes the equation's ``\\tag{n}`` (what
  ``block_roles.numbered_label`` reads). Two candidates are never guessed
  between, and an equation whose recognised text already ends with that
  number is left alone.

pdfium is not thread-safe, and the Reader renders PDF pages with it in the
sidecar's own process while an import reads in the background: so the
import's pdfium work (this text layer, and the page images a self-hosted
server is shown) runs in a worker process of its own (``pdfium_worker``).

A scan has no text layer: nothing is recovered and the reading says so.
Everything here is local and best-effort: a page pdfium can't read counts
as a page without a text layer, and a worker that fails, crashes or runs
out of time recovers nothing, never failing the extraction.
"""

from __future__ import annotations

import base64
import importlib.util
import io
import json
import re
import statistics
import subprocess
import sys
import unicodedata
from collections import Counter
from collections.abc import Callable, Sequence
from typing import Any, NamedTuple

NO_TEXT_LAYER = "glm_ocr_no_text_layer"
PARTIAL_TEXT_LAYER = "glm_ocr_text_layer_missing_on_some_pages"
TEXT_LAYER_UNAVAILABLE = "glm_ocr_text_layer_unavailable"
FOOTNOTES_RECOVERED = "glm_ocr_footnotes_from_text_layer"
EQUATION_NUMBERS_RECOVERED = "glm_ocr_equation_numbers_from_text_layer"

# A footnote starts in the lower part of the page (fraction of its height).
_FOOTNOTE_ZONE = 0.6
# A running line (header or footer) sits in the top or bottom margin
# (fraction of the page's height), is short, and comes back at the same
# height (points) on another page read.
_RUNNING_MARGIN = 0.12
_RUNNING_CHARS = 100
_RUNNING_HEIGHT = 2.0
_SUPERSCRIPT = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
_MARKER = re.compile(r"^(?:\d{1,3}|[*∗†‡§¶]{1,3}|[a-z])$")
_SYMBOL_MARK = re.compile(r"^(?:[*∗†‡§¶]{1,3}|[⁰¹²³⁴⁵⁶⁷⁸⁹]{1,3})\s*\S")
# A page number ("7", "- 7 -", "Page 7 of 9"), or a bare number like it ("33.",
# an exercise's number set in the margin): never a footnote's text.
_PAGE_NUMBER = re.compile(
    r"^(?:page\s+)?[\[(\-–—\s]*(?:\d{1,4}|[ivxlcdm]{1,8})[\]).\-–—\s]*(?:(?:of|/)\s*\d{1,4})?$", re.IGNORECASE
)
_EQUATION_NUMBER = re.compile(r"^\(\s*(\d+(?:\.\d+)*[a-z]?|[A-Z]\.\d+(?:\.\d+)*)\s*\)$")
# A display's recognised text ending with a number in brackets: its label,
# or its own maths ("f(0)").
_TRAILING_NUMBER = re.compile(r"\(\s*(\d+(?:\.\d+)*[a-z]?|[A-Z]\.\d+(?:\.\d+)*)\s*\)\s*(?:\$\$|\\\])$")
_DISPLAY_ENVIRONMENT = re.compile(r"\\begin\{(?:align|equation|gather|multline|eqnarray|flalign)\*?\}")
_ALNUM = re.compile(r"[^0-9a-z]+")


class TextSegment(NamedTuple):
    """One text run of a PDF page in the Reader's points (top-left origin)."""

    x0: float
    top: float
    x1: float
    bottom: float
    text: str


class TextRun(NamedTuple):
    """Segments of one line that sit together (a column's line, a number in
    the margin), joined into text."""

    x0: float
    top: float
    x1: float
    bottom: float
    text: str
    height: float
    marked: bool  # it opens with a footnote marker


PageTextLayer = Callable[[int], Sequence[TextSegment] | None]


def text_layer_engine() -> str:
    """What reads a PDF's text layer here: part of the extractor's identity,
    since it decides whether footnotes and equation numbers come back."""

    try:
        return "pdfium" if importlib.util.find_spec("pypdfium2") is not None else "none"
    except (ImportError, ValueError):
        return "none"


class PdfTextLayer:
    """``layer(page)``: the zero-based page's text segments, None when pdfium
    can't read the page. ``close()`` releases the document. Inside the
    pdfium worker only (``read_text_layer``)."""

    def __init__(self, document: Any):
        self._document = document

    def __call__(self, index: int) -> list[TextSegment] | None:
        try:
            page = self._document[index]
        except Exception:  # noqa: BLE001 - a page pdfium can't open has no text layer here
            return None
        try:
            crop = tuple(float(value) for value in page.get_cropbox())
            rotation = int(page.get_rotation() or 0) % 360
            textpage = page.get_textpage()
            try:
                segments = []
                for rect in range(textpage.count_rects()):
                    left, bottom, right, top = textpage.get_rect(rect)
                    # pdfium's bounded text takes every glyph the rectangle
                    # touches; inset it by a hair so a neighbour overlapping
                    # by 0.2 pt (a subscript's base: "fX" twice) is not read
                    # twice, while a closing full stop (~1 pt wide) stays.
                    inset = min(0.25 * (right - left), 0.4)
                    text = textpage.get_text_bounded(left=left + inset, bottom=bottom, right=right - inset, top=top)
                    text = _clean(text)
                    if text:
                        segments.append(_placed(left, bottom, right, top, text, crop, rotation))
                return segments
            finally:
                textpage.close()
        except Exception:  # noqa: BLE001 - best-effort: an unreadable page recovers nothing
            return None
        finally:
            page.close()

    def close(self) -> None:
        self._document.close()


# Old TeX fonts set an accent as its own glyph before the letter ("Th´eophile").
_SPACING_ACCENT = re.compile("([\u00b4\u00a8\u02c6\u02dc\u00b8])([A-Za-z])")
_COMBINING = {"\u00b4": "\u0301", "\u00a8": "\u0308", "\u02c6": "\u0302", "\u02dc": "\u0303", "\u00b8": "\u0327"}


def _clean(text: str) -> str:
    """A run's text: pdfium's hyphenation mark (\\x02) kept as a soft hyphen,
    spacing accents joined to their letter, whitespace collapsed."""

    text = _SPACING_ACCENT.sub(lambda match: match[2] + _COMBINING[match[1]], text.replace("\x02", "\u00ad"))
    return unicodedata.normalize("NFC", " ".join(text.split()))


def read_text_layer(raw: bytes, pages: Sequence[int]) -> tuple[PageTextLayer | None, str | None]:
    """The PDF's text layer on ``pages`` (zero-based), read by pdfium in a
    worker process; or None and the health flag saying why not (pypdfium2
    missing, a PDF pdfium can't open, a worker that crashed or ran out of
    time)."""

    if text_layer_engine() == "none":
        return None, TEXT_LAYER_UNAVAILABLE
    try:
        answer = pdfium_worker("text", raw, pages)
        read = {
            int(page): None if segments is None else [
                TextSegment(*(float(value) for value in segment[:4]), str(segment[4])) for segment in segments
            ]
            for page, segments in answer.items()
        }
    except (PdfiumWorkerError, AttributeError, TypeError, ValueError, IndexError):
        return None, TEXT_LAYER_UNAVAILABLE
    return read.get, None


# -- pdfium, in a worker process ----------------------------------------------------------
#
# pdfium is not thread-safe (pypdfium2: "PDFium is inherently not
# thread-safe"), and the Reader renders PDF pages with it in the sidecar's own
# process (reader/span_view.py) while an import runs on the ingest drain's
# thread. Two threads inside pdfium at once crashed the process with a
# segmentation fault (docs/reviews/glm-ocr-quality-codex-review.md, F1), which
# no Python exception handler contains. So the import never enters pdfium in
# this process: each reading starts one worker (``sys.executable``, the same
# environment), hands it the file on stdin and reads JSON back. A crash, a
# failure or a timeout stays in the worker.

_WORKER = "from learnloop.ingest.extractors.glm_text_layer import _worker_main; _worker_main()"
# Generous: Axler's 404 pages read in about 3 s in one process.
_WORKER_MIN_SECONDS = 120.0
_WORKER_SECONDS_PER_PAGE = 1.0


class PdfiumWorkerError(RuntimeError):
    """The worker could not do the pdfium work (pypdfium2 missing, a PDF
    pdfium can't open, a crash, a failure or a timeout)."""


def pdfium_worker(task: str, raw: bytes, pages: Sequence[int], **options: Any) -> Any:
    """Run ``task`` on the PDF ``raw`` in a worker process: "text", each
    page's text segments by page; "render", each page as a PNG data URI at
    ``scale``."""

    pages = [int(page) for page in pages]
    request = json.dumps({"task": task, "pages": pages, **options})
    timeout = max(_WORKER_MIN_SECONDS, _WORKER_SECONDS_PER_PAGE * len(pages))
    try:
        # -P: nothing in the working directory can stand in for a module.
        done = subprocess.run(
            [sys.executable, "-P", "-c", _WORKER, request], input=raw, capture_output=True, timeout=timeout,
            check=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError) as exc:  # TimeoutExpired: run() kills the worker
        raise PdfiumWorkerError(f"the pdfium worker did not finish ({type(exc).__name__})") from None
    if done.returncode != 0:
        raise PdfiumWorkerError(f"the pdfium worker stopped (exit {done.returncode})")
    try:
        answer = json.loads(done.stdout)
    except ValueError:
        raise PdfiumWorkerError("the pdfium worker's answer is not JSON") from None
    if not isinstance(answer, dict) or "result" not in answer:
        reason = answer.get("error") if isinstance(answer, dict) else None
        raise PdfiumWorkerError(f"the pdfium worker could not do it ({reason or 'no result'})")
    return answer["result"]


def _worker_main() -> None:
    """The worker's side: the request in ``sys.argv[1]``, the PDF on stdin,
    ``{"result": ...}`` or ``{"error": ...}`` on stdout."""

    request = json.loads(sys.argv[1])
    raw = sys.stdin.buffer.read()
    try:
        import pypdfium2 as pdfium
    except ImportError:
        sys.stdout.write(json.dumps({"error": "pypdfium2 is not installed"}))
        return
    try:
        document = pdfium.PdfDocument(raw)
    except Exception:  # noqa: BLE001 - pdfium can't open it
        sys.stdout.write(json.dumps({"error": "pdfium can't open the PDF"}))
        return
    try:
        result: Any
        if request["task"] == "text":
            layer = PdfTextLayer(document)
            result = {}
            for index in request["pages"]:
                segments = layer(index)
                result[str(index)] = None if segments is None else [list(segment) for segment in segments]
        elif request["task"] == "render":
            result = []
            for index in request["pages"]:
                page = document[index]
                try:
                    bitmap = page.render(scale=float(request["scale"]))
                    try:
                        out = io.BytesIO()
                        bitmap.to_pil().save(out, format="PNG")
                    finally:
                        bitmap.close()
                finally:
                    page.close()
                result.append("data:image/png;base64," + base64.b64encode(out.getvalue()).decode("ascii"))
        else:
            raise ValueError(f"unknown task {request['task']!r}")
    except Exception as exc:  # noqa: BLE001 - reported to the caller, which decides
        sys.stdout.write(json.dumps({"error": type(exc).__name__}))
        return
    finally:
        document.close()
    sys.stdout.write(json.dumps({"result": result}))


def _placed(left: float, bottom: float, right: float, top: float, text: str,
            crop: tuple[float, ...], rotation: int) -> TextSegment:
    """PDF user space -> the Reader's view: crop-box origin, top-left, rotated
    clockwise by the page's /Rotate like the page is shown."""

    crop_left, crop_bottom, crop_right, crop_top = crop
    width, height = crop_right - crop_left, crop_top - crop_bottom
    points = []
    for x, y in ((left, bottom), (right, top)):
        u, v = x - crop_left, y - crop_bottom
        if rotation == 90:
            points.append((v, u))
        elif rotation == 180:
            points.append((width - u, v))
        elif rotation == 270:
            points.append((height - v, width - u))
        else:
            points.append((u, height - v))
    (ax, ay), (bx, by) = points
    return TextSegment(round(min(ax, bx), 2), round(min(ay, by), 2), round(max(ax, bx), 2), round(max(ay, by), 2), text)


# -- lines and runs ---------------------------------------------------------------


def _height(item: Any) -> float:
    return max(float(item.bottom) - float(item.top), 0.1)


def text_runs(segments: Sequence[TextSegment]) -> list[TextRun]:
    """Segments grouped into lines, each line split into runs at wide gaps
    (a column gutter, a number in the margin).

    The tallest segments found the lines; a segment joins the line whose
    founding band holds its middle (or whose middle its band holds), so
    superscripts and subscripts stay on their line and lines never chain
    into one another."""

    lines: list[tuple[float, float, list[TextSegment]]] = []
    for segment in sorted(segments, key=lambda s: (-_height(s), s.top, s.x0)):
        middle = (segment.top + segment.bottom) / 2
        for top, bottom, members in lines:
            if top <= middle <= bottom or segment.top <= (top + bottom) / 2 <= segment.bottom:
                members.append(segment)
                break
        else:
            lines.append((segment.top, segment.bottom, [segment]))
    runs: list[TextRun] = []
    for _, _, line in lines:
        line.sort(key=lambda s: s.x0)
        typical = statistics.median(_height(s) for s in line)
        gap_limit = max(1.5 * typical, 8.0)
        current = [line[0]]
        for segment in line[1:]:
            if segment.x0 - max(s.x1 for s in current) > gap_limit:
                runs.append(_run(current))
                current = [segment]
            else:
                current.append(segment)
        runs.append(_run(current))
    return sorted(runs, key=lambda r: (r.top, r.x0))


def _run(segments: list[TextSegment]) -> TextRun:
    body = segments
    lead = ""
    if len(segments) > 1:
        first, second = segments[0], segments[1]
        raised = (_height(first) <= 0.8 * _height(second)
                  and first.bottom < second.bottom - 0.15 * _height(second))
        if _MARKER.match(first.text) and raised:
            # A raised footnote mark: "¹ See ..." (digits as superscripts).
            body = segments[1:]
            lead = first.text.translate(_SUPERSCRIPT) + " "
    text = body[0].text
    for previous, segment in zip(body, body[1:]):
        # pdfium keeps a word space inside its run; a narrow gap is a font
        # change inside a word or a number ("0" "." "51").
        gap = segment.x0 - previous.x1
        joiner = " " if gap >= 0.25 * max(_height(previous), _height(segment)) else ""
        text += joiner + segment.text
    text = lead + " ".join(text.split())
    marked = bool(lead) or bool(_SYMBOL_MARK.match(text))
    heights = [_height(s) for s in body]
    return TextRun(
        x0=min(s.x0 for s in segments), top=min(s.top for s in segments),
        x1=max(s.x1 for s in segments), bottom=max(s.bottom for s in segments),
        text=text, height=statistics.median(heights), marked=marked,
    )


# -- the pages read -------------------------------------------------------------------


class PageTexts:
    """The text segments and runs of every page read, and the running lines
    among them: headers and footers, short lines in the top or bottom margin
    that come back at the same height on another page read (digits stand for
    any number). The same words in a page's body never make a line running
    (a footnote's "See Chapter 2 for the proof." that the text also says
    elsewhere stays in the footnote)."""

    def __init__(self, layer: PageTextLayer, pages: Sequence[int], heights: Callable[[int], float]):
        self._pages: dict[int, tuple[list[TextSegment], list[TextRun]] | None] = {}
        for page in dict.fromkeys(pages):
            try:
                segments = list(layer(page) or ())
            except Exception:  # noqa: BLE001 - best-effort, as for an unreadable page
                segments = []
            self._pages[page] = (segments, text_runs(segments)) if segments else None
        marginal: dict[str, list[tuple[float, int]]] = {}
        for page, read in self._pages.items():
            height = heights(page)
            for run in read[1] if read else ():
                key = _running_key(run.text)
                if key and len(run.text) <= _RUNNING_CHARS and (
                    run.bottom <= _RUNNING_MARGIN * height or run.top >= (1 - _RUNNING_MARGIN) * height
                ):
                    marginal.setdefault(key, []).append((run.top, page))
        # key -> the heights it runs at (on two pages or more)
        self._running: dict[str, list[float]] = {}
        for key, places in marginal.items():
            places.sort()
            start = 0
            for top, page in places:
                while places[start][0] < top - _RUNNING_HEIGHT:
                    start += 1
                other = start
                while other < len(places) and places[other][0] <= top + _RUNNING_HEIGHT:
                    if places[other][1] != page:
                        self._running.setdefault(key, []).append(top)
                        break
                    other += 1

    def segments(self, page: int) -> list[TextSegment] | None:
        read = self._pages.get(page)
        return read[0] if read else None

    def runs(self, page: int) -> list[TextRun] | None:
        read = self._pages.get(page)
        return read[1] if read else None

    def is_furniture(self, run: TextRun) -> bool:
        """A page number, or a running line where it runs."""

        if _PAGE_NUMBER.match(run.text.strip()):
            return True
        return any(abs(run.top - top) <= _RUNNING_HEIGHT for top in self._running.get(_running_key(run.text), ()))


def _running_key(text: str) -> str:
    return " ".join(re.sub(r"\d+", "#", text.lower()).split())


def _normalised(text: str) -> str:
    return _ALNUM.sub("", text.lower())


def _x_overlap(a: Any, b: Sequence[float]) -> float:
    return min(a.x1, b[2]) - max(a.x0, b[0])


def _inside(run: Any, box: Sequence[float], tolerance: float = 1.5) -> bool:
    """Whether most of ``run`` lies inside ``box``."""

    width = min(run.x1, box[2] + tolerance) - max(run.x0, box[0] - tolerance)
    height = min(run.bottom, box[3] + tolerance) - max(run.top, box[1] - tolerance)
    area = max(run.x1 - run.x0, 0.1) * max(run.bottom - run.top, 0.1)
    return width > 0 and height > 0 and width * height >= 0.5 * area


# -- equation numbers -------------------------------------------------------------------


def _set_apart(segment: TextSegment, segments: Sequence[TextSegment]) -> bool:
    """Whether a "(n)" stands apart on its line, as an equation number does
    (flush right, set off from the display), unlike "F (2)" or "M(0)" inside
    a formula, whose neighbours sit a thin space away (1.4-2.4 pt in the
    live books, against 6.7 pt and more for a number)."""

    height = _height(segment)
    space = max(0.5 * height, 3.0)
    for other in segments:
        if other is segment or min(other.bottom, segment.bottom) - max(other.top, segment.top) < 0.5 * min(
            height, _height(other)
        ):
            continue
        if segment.x0 - space < other.x1 <= segment.x0 + 0.5 or segment.x1 - 0.5 <= other.x0 < segment.x1 + space:
            return False
    return True


class EquationNumber(NamedTuple):
    """A display's number from the text layer, and whether it lies beside
    the display's region rather than in it (then the recognised text can't
    hold it)."""

    number: str
    beside: bool


def equation_numbers(
    segments: Sequence[TextSegment] | None,
    equations: dict[int, Sequence[float]],
    boxes: Sequence[Sequence[float] | None],
) -> dict[int, EquationNumber]:
    """The number to tag each display region with, by region position.

    ``equations``: position -> box of each display region; ``boxes``: every
    region's box on the page (by position). A number "(n)" standing apart on
    its line counts for a display when its middle is in the display's band,
    it sits in the display's right half or beyond with no other region in
    between, inside no other region, and it is the only such number for that
    display and that display the only one for it."""

    if not segments or not equations:
        return {}
    numbers = [(index, segment, _EQUATION_NUMBER.match(segment.text)) for index, segment in enumerate(segments)]
    numbers = [(index, segment, match[1]) for index, segment, match in numbers
               if match and _set_apart(segment, segments)]
    candidates: dict[int, list[tuple[int, str]]] = {}
    claimed: Counter[int] = Counter()
    for position, box in equations.items():
        found = []
        for index, segment, number in numbers:
            height = _height(segment)
            middle = (segment.top + segment.bottom) / 2
            if not box[1] - 0.6 * height <= middle <= box[3] + 0.6 * height:
                continue
            if segment.x0 < (box[0] + box[2]) / 2:
                continue
            others = [other for other_position, other in enumerate(boxes)
                      if other is not None and other_position != position]
            if any(_inside(segment, other) for other in others):
                continue  # it belongs to the text it sits in
            if any(min(other[3], box[3]) > max(other[1], box[1]) and other[0] < segment.x0 and other[2] > box[2]
                   for other in others):
                continue  # another region (the next column) lies between them
            found.append((index, EquationNumber(number, not _inside(segment, box))))
        candidates[position] = found
        claimed.update(index for index, _ in found)
    return {position: found[0][1] for position, found in candidates.items()
            if len(found) == 1 and claimed[found[0][0]] == 1}


def with_equation_tag(text: str, number: EquationNumber) -> str | None:
    """``text`` (a display, ``$$...$$`` or ``\\[...\\]``) tagged with
    ``number``, or None when it already carries a number or can't take one.

    A display carries its number when it has a ``\\tag``, or when it ends
    with that very number in brackets and the number lies in its region (the
    recognition read it). Its own maths ending in brackets ("f(0)") is no
    number: then the tag goes on."""

    stripped = text.strip()
    if "\\tag" in stripped or _DISPLAY_ENVIRONMENT.search(stripped):
        return None
    trailing = _TRAILING_NUMBER.search(stripped)
    if trailing and not number.beside and trailing[1].replace(" ", "") == number.number:
        return None
    for opener, closer in (("$$", "$$"), ("\\[", "\\]")):
        if stripped.startswith(opener) and stripped.endswith(closer) and len(stripped) > len(opener) + len(closer):
            body = stripped[len(opener):-len(closer)]
            if body.endswith("\n"):
                return f"{opener}{body[:-1]} \\tag{{{number.number}}}\n{closer}"
            return f"{opener}{body} \\tag{{{number.number}}}{closer}"
    return None


# -- footnotes ----------------------------------------------------------------------------


def footnotes(
    runs: Sequence[TextRun] | None,
    boxes: Sequence[Sequence[float] | None],
    page_size: tuple[float, float],
    present: str,
    *,
    is_furniture: Callable[[TextRun], bool],
) -> list[tuple[list[float], str]]:
    """Footnotes the answer lacks on one page, as (box, text) in reading order.

    ``boxes``: every region's box on the page; ``present``: the text of the
    page's blocks, never repeated."""

    if not runs:
        return []
    regions = [box for box in boxes if box is not None]
    if not regions:
        return []
    width, height = page_size
    seen = _Seen(present)
    candidates = []
    for run in runs:
        if run.top < _FOOTNOTE_ZONE * height or run.top >= height or run.x0 >= width:
            continue
        if any(_inside(run, box) for box in regions):
            continue
        overlapping = [box for box in regions if _x_overlap(run, box) > 0.2 * min(run.x1 - run.x0, box[2] - box[0])]
        if not overlapping or any(box[3] > run.top + 2.0 for box in overlapping):
            continue  # not below everything in its column
        column = max(overlapping, key=lambda box: box[3])
        if run.x0 > column[0] + max(0.2 * (column[2] - column[0]), 24.0):
            continue  # a note beside the text (a margin note), not under its column
        if run.top - column[3] < 0.5 * (run.bottom - run.top):
            continue  # it runs on from the region above (a line the answer dropped), set off by no gap
        if is_furniture(run) or _EQUATION_NUMBER.match(run.text):
            continue
        if _already_read(_lead_stripped(run), seen):
            continue
        candidates.append(run)

    groups: list[list[TextRun]] = []
    for run in candidates:
        group = next((
            group for group in reversed(groups)
            if not run.marked
            and min(run.x1, max(r.x1 for r in group)) - max(run.x0, min(r.x0 for r in group)) > 0
            and 0 <= run.top - max(r.bottom for r in group) <= 0.8 * max(run.height, group[-1].height)
        ), None)
        if group is None:
            groups.append([run])
        else:
            group.append(run)

    found = []
    for group in groups:
        text = group[0].text
        for run in group[1:]:
            if text.endswith("\u00ad") and run.text[:1].islower():
                text = text[:-1] + run.text  # a word hyphenated at the line's end
            elif text.endswith(("\u00ad", "-")):
                text = text[:-1] + "-" + run.text  # a hyphen of its own ("Jean-Paul")
            else:
                text += " " + run.text
        text = text.replace("\u00ad", "-").strip()
        if not text or _already_read(re.sub(r"^\S{1,3}\s", "", text) if group[0].marked else text, seen):
            continue
        box = [min(r.x0 for r in group), min(r.top for r in group), max(r.x1 for r in group), max(r.bottom for r in group)]
        box = [round(max(0.0, min(box[0], width)), 2), round(max(0.0, min(box[1], height)), 2),
               round(max(0.0, min(box[2], width)), 2), round(max(0.0, min(box[3], height)), 2)]
        # The text layer is plain text: a dollar is a dollar, never maths.
        found.append((box, text.replace("$", "\\$")))
    return found


def _lead_stripped(run: TextRun) -> str:
    return re.sub(r"^\S{1,3}\s", "", run.text) if run.marked else run.text


_LATEX = re.compile(r"\\[A-Za-z]+")
_WORDS = re.compile(r"[a-z]{3,}")


class _Seen:
    """The text a page's blocks already hold, to never repeat it: its
    letters and digits, and the pairs of consecutive words (three letters or
    more, LaTeX commands dropped, so "$ v_{2}, \\ldots $" and "𝑣2 , …" agree)."""

    def __init__(self, text: str):
        self.flat = _normalised(text)
        words = _WORDS.findall(_LATEX.sub(" ", text).lower())
        self.pairs = set(zip(words, words[1:]))


def _already_read(text: str, seen: _Seen) -> bool:
    words = _WORDS.findall(_LATEX.sub(" ", text).lower())
    if len(words) >= 3:
        pairs = list(zip(words, words[1:]))
        if sum(pair in seen.pairs for pair in pairs) >= 0.75 * len(pairs):
            return True
    key = _normalised(text)
    return len(key) >= 4 and key in seen.flat


__all__ = [
    "EQUATION_NUMBERS_RECOVERED",
    "FOOTNOTES_RECOVERED",
    "NO_TEXT_LAYER",
    "PARTIAL_TEXT_LAYER",
    "EquationNumber",
    "PageTexts",
    "PdfTextLayer",
    "PdfiumWorkerError",
    "TEXT_LAYER_UNAVAILABLE",
    "TextRun",
    "TextSegment",
    "equation_numbers",
    "footnotes",
    "pdfium_worker",
    "read_text_layer",
    "text_layer_engine",
    "text_runs",
    "with_equation_tag",
]
