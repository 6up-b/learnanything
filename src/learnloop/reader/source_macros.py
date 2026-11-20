"""A source's own TeX macros, read from its stored original for the page's renderers.

A web chapter defines its notation once (PreTeXt puts ``\\newcommand{\\vvec}{{\\mathbf v}}`` and
sixty more in a hidden ``#latex-macros`` element) and uses it in every formula. The extraction
keeps the formulas and drops the definitions: the readable-body extractor skips hidden elements.
So the blocks hold ``\\vvec`` with nothing to define it, and KaTeX shows it as a red raw command
(or ``\\real`` as its own built-in ℜ instead of the book's ℝ).

The definitions are read here from the original bytes the vault keeps for every revision
(``canonical-sources/raw/``), at read time, and handed to the renderers as KaTeX's ``macros``
option. Nothing stored changes: block text, block and extraction hashes, render views and
everything sent to a model stay as they were, and a source added before this existed gets its
macros the first time it is opened, with no re-read and no model.

The document is untrusted. Only ``\\newcommand``, ``\\renewcommand``, ``\\providecommand`` and
``\\def`` with plain ``#1..#9`` parameters are read; counts, name and body lengths are bounded;
a body that would define, include, read, write or re-catcode anything is dropped. A body is
only ever text handed to KaTeX as a macro, never expanded or evaluated here, and KaTeX's own
expansion limit (``maxExpand``) stays in force, so a recursive macro is an error in the one
formula that uses it.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from learnloop.content.sources.exam_material import exam_material
from learnloop.ingest.originals import PDF_MAGIC, stored_original_path

LOG = logging.getLogger(__name__)

#: keep (bounds an untrusted document): at most this many macros per source. PreTeXt books carry
#: about 60-120; past the cap the rest are ignored, never an error.
MAX_MACROS = 256
#: keep (bounds an untrusted document): a macro name's letters, without the backslash.
MAX_NAME_LENGTH = 40
#: keep (bounds an untrusted document): one body's characters. The sample's longest is about 330.
MAX_BODY_LENGTH = 2000
#: keep (bounds an untrusted document): every body together, so the reply stays small.
MAX_TOTAL_BODY = 64_000
#: keep (bounds the read): an original larger than this is not scanned for definitions.
MAX_ORIGINAL_BYTES = 16_000_000

_DEFINER = re.compile(r"\\(newcommand|renewcommand|providecommand|def)(?![A-Za-z@])(\*?)")
_NAME = re.compile(r"\\([A-Za-z]+)(?![A-Za-z@])")
#: A body that names any of these could define, include, read, write or re-catcode something in the
#: renderer, or reach a resource: it is dropped whole. (KaTeX refuses most of them anyway; this keeps
#: the table itself inert, whatever a later KaTeX accepts.)
_FORBIDDEN_IN_BODY = re.compile(
    r"\\(?:def|gdef|edef|xdef|let|futurelet|global|long|outer|newcommand|renewcommand|providecommand"
    r"|input|include|includeonly|InputIfFileExists|openin|openout|read|readline|write|immediate|special"
    r"|catcode|lccode|uccode|sfcode|mathcode|delcode|csname|endcsname|expandafter|noexpand|afterassignment"
    r"|href|url|includegraphics|htmlClass|htmlId|htmlStyle|htmlData)(?![A-Za-z@])"
)
_LOOKS_HTML = re.compile(rb"\s*(?:<!doctype\s+html|<html|<head|<body|<div|<meta)", re.IGNORECASE)


def parse_tex_macros(text: str) -> dict[str, str]:
    """The macro table the definitions in ``text`` make, as KaTeX's ``macros`` option takes it
    (``{"\\\\vvec": "{\\\\mathbf v}"}``). A later definition of a name replaces an earlier one, as
    ``\\renewcommand`` does. A definition outside the bounds or the allowed forms is skipped."""

    macros: dict[str, str] = {}
    total = 0
    position = 0
    while len(macros) < MAX_MACROS:
        match = _DEFINER.search(text, position)
        if match is None:
            break
        position = match.end()
        parsed = (_read_def if match.group(1) == "def" else _read_newcommand)(text, position)
        if parsed is None:
            continue
        name, body, position = parsed
        if len(body) > MAX_BODY_LENGTH or _FORBIDDEN_IN_BODY.search(body):
            continue
        if total + len(body) > MAX_TOTAL_BODY:
            break
        if match.group(1) == "providecommand" and f"\\{name}" in macros:
            continue
        total += len(body)
        macros[f"\\{name}"] = body
    return macros


def _skip_space(text: str, at: int) -> int:
    while at < len(text) and text[at] in " \t\r\n":
        at += 1
    return at


def _read_name(text: str, at: int) -> tuple[str, int] | None:
    """``\\name`` or ``{\\name}`` at ``at``: the letters and the index after it."""

    at = _skip_space(text, at)
    braced = at < len(text) and text[at] == "{"
    if braced:
        at = _skip_space(text, at + 1)
    match = _NAME.match(text, at)
    if match is None or len(match.group(1)) > MAX_NAME_LENGTH:
        return None
    at = match.end()
    if braced:
        at = _skip_space(text, at)
        if at >= len(text) or text[at] != "}":
            return None
        at += 1
    return match.group(1), at


def _read_group(text: str, at: int) -> tuple[str, int] | None:
    """A balanced ``{...}`` at ``at`` (escaped braces do not count): its inside and the index after it.
    Gives up past the body bound, so an unclosed brace never scans the rest of a page."""

    if at >= len(text) or text[at] != "{":
        return None
    depth = 0
    index = at
    limit = min(len(text), at + MAX_BODY_LENGTH + 2)
    while index < limit:
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[at + 1:index], index + 1
        index += 1
    return None


def _read_newcommand(text: str, at: int) -> tuple[str, str, int] | None:
    named = _read_name(text, at)
    if named is None:
        return None
    name, at = named
    at = _skip_space(text, at)
    arguments = 0
    if at < len(text) and text[at] == "[":
        close = text.find("]", at, at + 4)
        if close < 0 or not text[at + 1:close].strip().isdigit():
            return None
        arguments = int(text[at + 1:close].strip())
        if not 0 <= arguments <= 9:
            return None
        at = _skip_space(text, close + 1)
        if at < len(text) and text[at] == "[":
            # An optional argument's default: KaTeX's macro table has no way to say it.
            return None
    group = _read_group(text, at)
    if group is None:
        return None
    body, end = group
    if _highest_parameter(body) > arguments:
        return None
    return name, body, end


def _read_def(text: str, at: int) -> tuple[str, str, int] | None:
    match = _NAME.match(text, _skip_space(text, at))
    if match is None or len(match.group(1)) > MAX_NAME_LENGTH:
        return None
    at = match.end()
    # Only undelimited parameters, in order: ``#1#2{...}``. A delimited one (``#1.``) changes how
    # arguments are read, which a KaTeX string macro cannot say.
    expected = 1
    while at + 1 < len(text) and text[at] == "#":
        if text[at + 1] != str(expected):
            return None
        expected += 1
        at += 2
    group = _read_group(text, at)
    if group is None:
        return None
    body, end = group
    if _highest_parameter(body) > expected - 1:
        return None
    return match.group(1), body, end


def _highest_parameter(body: str) -> int:
    found = [int(digit) for digit in re.findall(r"(?<!#)#([1-9])", body.replace("##", ""))]
    return max(found, default=0)


class _VisibleAndHiddenText(HTMLParser):
    """The page's text, hidden elements included (that is where the definitions live), with
    entities decoded (``\\newcommand{\\amp}{&amp;}`` is ``&`` to TeX). Scripts and styles are
    left out: a definition quoted in a script's string is the script's, not the page's."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skipping = 0

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        if tag in {"script", "style"}:
            self._skipping += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skipping:
            self._skipping -= 1

    def handle_data(self, data: str) -> None:
        if not self._skipping:
            self._parts.append(data)

    def text(self) -> str:
        return "".join(self._parts)


def macros_from_original(raw: bytes) -> dict[str, str]:
    """The macro table of one original's bytes: an HTML page's text, or a text file's own
    (Markdown or TeX); nothing for a PDF, an image, audio or anything else binary."""

    if not raw or len(raw) > MAX_ORIGINAL_BYTES or raw.startswith(PDF_MAGIC) or b"\x00" in raw[:4096]:
        return {}
    text = raw.decode("utf-8", errors="replace")
    if "\\" not in text:
        return {}
    if _LOOKS_HTML.match(raw[:4096]):
        parser = _VisibleAndHiddenText()
        parser.feed(text)
        parser.close()
        text = parser.text()
    return parse_tex_macros(text)


@lru_cache(maxsize=64)
def _cached_macros(path: str, digest: str) -> tuple[tuple[str, str], ...]:
    # Keyed by the content hash the stored file's name commits to: the same bytes, the same table.
    try:
        raw = Path(path).read_bytes()
    except OSError:
        return ()
    return tuple(macros_from_original(raw).items())


def source_math_macros(vault_root: Path, revision: dict[str, Any] | None) -> dict[str, str]:
    """The macros of a revision's stored original, or ``{}`` when it has none or the original is not
    in the vault's store. Read only: a missing original is not backfilled here."""

    digest = str((revision or {}).get("asset_hash") or "")
    path = stored_original_path(vault_root, digest)
    if path is None:
        return {}
    return dict(_cached_macros(str(path), digest))


def extraction_math_macros(vault: Any, repository: Any, extraction_id: str | None) -> dict[str, str]:
    """The macros of the source an extraction was read from (see :func:`source_math_macros`), or ``{}``
    while anything of that source is protected.

    The table comes from the whole original, so a definition in a withheld part (a past paper's solutions,
    a held-out unit: ``\\newcommand{\\ans}{x = 3}``) would otherwise reach a view of another part. Where the
    definitions sit is not mapped to spans, so one protected passage anywhere withholds the whole table."""

    run = repository.get_extraction_run(extraction_id) if extraction_id else None
    revision = repository.get_source_revision(run["revision_id"]) if run and run.get("revision_id") else None
    macros = source_math_macros(vault.root, revision)
    if not macros or _anything_protected(vault, repository, revision or {}):
        return {}
    return macros


def _anything_protected(vault: Any, repository: Any, revision: dict[str, Any]) -> bool:
    """Whether exam material (rules 1-4, the held-out partition included: the predicate the phone's
    ``phone_withheld`` and the Reader's section withholding read) covers any reading of this source, or
    of the same original under another source, wholly or in part. Fails closed: a predicate that cannot
    be read counts as protected."""

    try:
        material = exam_material(vault, repository)
        with repository.connection() as connection:
            rows = connection.execute(
                "SELECT r.id FROM source_extraction_runs r JOIN source_revisions v ON v.id = r.revision_id "
                "WHERE v.source_id = ? OR v.asset_hash = ?",
                (str(revision.get("source_id") or ""), str(revision.get("asset_hash") or "")),
            ).fetchall()
    except Exception:  # noqa: BLE001 - fail closed: an unreadable predicate sends no table
        LOG.exception("exam material unreadable; no math macros for revision %s", revision.get("id"))
        return True
    return bool({str(row[0]) for row in rows} & material.material.touched)


__all__ = [
    "MAX_BODY_LENGTH",
    "MAX_MACROS",
    "MAX_NAME_LENGTH",
    "MAX_TOTAL_BODY",
    "extraction_math_macros",
    "macros_from_original",
    "parse_tex_macros",
    "source_math_macros",
]
