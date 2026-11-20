"""A web page read into Markdown (extractor ``html``).

Version "2" is trafilatura's readable body (:func:`readable_markdown`); pages read with it keep that reading.
Version "3" (:func:`page_markdown`) is what a new read of a web page uses. On a page made of many ``<article>``
elements (a PreTeXt book's section: its activities, examples and exercises are articles), trafilatura takes the
first article for the whole page, finds it short and falls back to a generic extractor that keeps only paragraphs
with enough words: 31 of the sample chapter's 34 display equations, the matrices of its exercise lists and every
heading were lost there. Version 3 calls trafilatura the same way on the same page, after named, bounded changes
to the parsed page (:func:`prepare_page`), and tidies two marks of its Markdown writer (:func:`_tidy`).

Display math is left as the page writes it (a bare ``\\begin{equation*}`` environment, ``\\[ \\]``, ``$$``): the
renderers draw those already. MathML and MathJax's script math, which trafilatura drops, become ``\\( \\)`` and
``\\[ \\]`` TeX.
"""

from __future__ import annotations

import re
from typing import Any

#: The extractor version a new read of a web page records (``default_extraction_identity``); "2" is the version
#: pages read before keep, and the one the Library offers to read again.
WEB_PAGE_EXTRACTOR_VERSION = "3"
OLD_WEB_PAGE_EXTRACTOR_VERSION = "2"

#: A page's own furniture, by class: removed whole before reading, so no other element and no body text goes.
PAGE_FURNITURE = {
    "mw-editsection": "MediaWiki's [edit] link beside a section heading",
    "ambox": "MediaWiki's article maintenance notices (\"This article has multiple issues…\")",
}

_HIDDEN_XPATH = (
    "//details[not(@open)] | //*[@hidden] | //*[@aria-hidden='true'] | //template"
    " | //*[contains(translate(@style, ' ', ''), 'display:none')]"
    " | //*[contains(translate(@style, ' ', ''), 'visibility:hidden')]"
)
#: A hidden part shorter than this many letters and digits is always left out: so short a string can match the
#: old reading's text by chance (an answer "42").
_HIDDEN_MATCH_MIN = 12

_TEX = "application/x-tex"
#: The TeX environments that are display math by themselves (a matrix environment is not: it sits inside one,
#: or inside inline math).
_DISPLAY_ENVIRONMENT = r"(?:equation|align|alignat|gather|multline|flalign|eqnarray|displaymath)\*?"


def readable_markdown(raw_html: Any) -> str | None:
    """Version 2: trafilatura's readable body as Markdown."""

    try:
        import trafilatura
    except ImportError:  # pragma: no cover - trafilatura is a base dependency
        return None
    extracted = trafilatura.extract(raw_html, output_format="markdown", include_tables=True, include_comments=False)
    return extracted or None


def page_markdown(raw_html: str) -> str | None:
    """Version 3: the page's readable body as Markdown, its display math, headings and lists kept."""

    from trafilatura.utils import load_html

    tree = load_html(raw_html)
    if tree is None:
        return readable_markdown(raw_html)
    headings = {_squeeze(heading.text_content()) for heading in tree.xpath("//h1|//h2|//h3|//h4|//h5|//h6")}
    prepare_page(tree, old_text=readable_markdown(raw_html) or "")
    markdown = readable_markdown(tree)
    return _tidy(markdown, headings) if markdown else None


def prepare_page(tree: Any, *, old_text: str) -> None:
    """The changes version 3 makes to a parsed page before trafilatura reads it, in order."""

    _mediawiki_formulas_as_tex(tree)
    _hidden_parts_as_before(tree, old_text)
    _drop_furniture(tree)
    _math_as_tex(tree)
    _articles_as_parts(tree)


def _mediawiki_formulas_as_tex(tree: Any) -> None:
    """A MediaWiki formula shows as an image whose TeX is also in a hidden MathML copy: its TeX, as math."""

    for element in tree.xpath('//*[contains(concat(" ", normalize-space(@class), " "), " mwe-math-element ")]'):
        tex = _annotation(element) or next(iter(element.xpath(".//img/@alt")), None)
        if not tex:
            continue
        tex = re.sub(r"^\s*\{\\displaystyle\s*(.*)\}\s*$", r"\1", tex, flags=re.DOTALL).strip()
        display = bool(element.xpath('.//*[contains(@class, "-display")] | .//*[@display="block"]'))
        _replace_with_text(element, _delimited(tex, display))


def _hidden_parts_as_before(tree: Any, old_text: str) -> None:
    """A hidden or collapsed part reaches the text only where version 2 let it: version 3 reads more of some
    pages than version 2 did, and a solution a page hides behind a disclosure must not start reaching the text
    that way. Each hidden part whose letters and digits are not in the old reading is removed; for a closed
    ``<details>`` the hidden part is its body (its ``<summary>`` shows)."""

    old = _letters(old_text)
    for element in tree.xpath(_HIDDEN_XPATH):
        if element.getparent() is None:
            continue
        hidden = _letters("".join(
            text for text in element.xpath(".//text()[not(ancestor::summary)]") if isinstance(text, str)
        )) if element.tag == "details" else _letters(element.text_content())
        if not hidden:
            continue
        if len(hidden) < _HIDDEN_MATCH_MIN or hidden not in old:
            _remove(element)


def _drop_furniture(tree: Any) -> None:
    for name in PAGE_FURNITURE:
        for element in tree.xpath(f'//*[contains(concat(" ", normalize-space(@class), " "), " {name} ")]'):
            _remove(element)


def _math_as_tex(tree: Any) -> None:
    """MathML with its TeX (a TeX annotation, else ``alttext``) and MathJax's ``math/tex`` scripts, as TeX."""

    for element in tree.xpath('//*[local-name()="math"]'):
        if element.getparent() is None:
            continue
        tex = _annotation(element) or (element.get("alttext") or "").strip()
        if tex:
            _replace_with_text(element, _delimited(tex, element.get("display") == "block"))
    for script in tree.xpath('//script[starts-with(@type, "math/tex")]'):
        tex = (script.text or "").strip()
        if tex:
            _replace_with_text(script, _delimited(tex, "mode=display" in (script.get("type") or "")))


def _articles_as_parts(tree: Any) -> None:
    """When the page's first ``<article>`` holds under half of its main text, the articles are parts of the page
    (a book's activities and exercises), not the page: they are read as the page's other blocks are."""

    articles = tree.xpath("//article")
    if not articles:
        return
    container = next(iter(tree.xpath("//main")), None)
    if container is None:
        container = next(iter(tree.xpath("//body")), tree)
    if len(_letters(articles[0].text_content())) * 2 >= len(_letters(container.text_content())):
        return
    for article in articles:
        article.tag = "div"


def _tidy(markdown: str, headings: set[str]) -> str:
    """Two marks of trafilatura's Markdown writer: a heading written at the end of the line before it (after
    emphasis that closes a paragraph) is put on its own line, when its words are a heading of the page; a list
    item whose text starts in a child element is written "-" alone on a line, and is joined to its text."""

    lines: list[str] = []
    for line in markdown.split("\n"):
        marks = [] if line.startswith("#") else list(re.finditer(r"(?<=[^#\s])(#{1,6}) ", line))
        glued = next((mark for mark in reversed(marks) if _squeeze(line[mark.end():]) in headings), None)
        if glued is not None:
            lines.extend([line[:glued.start()], "", f"{glued.group(1)} {line[glued.end():].strip()}"])
        else:
            lines.append(line)
    joined: list[str] = []
    for line in lines:
        if joined and joined[-1] == "-" and line.strip() and not re.match(r"\s*(#|-|\||\\begin|\\\[|\$\$)", line):
            joined[-1] = f"- {line}"
        else:
            joined.append(line)
    return "\n".join(_displays_apart(joined))


def _displays_apart(lines: list[str]) -> list[str]:
    """A display environment trafilatura wrote on the lines after a paragraph's last words (or before the next
    paragraph's first) is set apart by a blank line, so it is a block of its own as the page shows it."""

    out: list[str] = []
    closing: str | None = None
    apart = False
    for line in lines:
        if closing is None:
            opened = re.match(rf"\\begin\{{({_DISPLAY_ENVIRONMENT})\}}", line)
            if apart and line.strip():
                out.append("")
            apart = False
            if opened:
                if out and out[-1].strip():
                    out.append("")
                closing = f"\\end{{{opened.group(1)}}}"
        out.append(line)
        if closing is not None and line.startswith(closing):
            closing, apart = None, True
    return out


def display_formulas(markdown: str) -> list[str]:
    """The display formulas of version-3 Markdown, in order: bare display environments, ``\\[ \\]`` and
    ``$$ $$``."""

    pattern = re.compile(rf"(?s)\\begin\{{({_DISPLAY_ENVIRONMENT})\}}.*?\\end\{{\1\}}|\\\[.+?\\\]|\$\$.+?\$\$")
    return [match.group(0) for match in pattern.finditer(markdown)]


def _annotation(element: Any) -> str | None:
    for annotation in element.xpath('.//*[local-name()="annotation"]'):
        if (annotation.get("encoding") or "").lower() == _TEX and (annotation.text or "").strip():
            return annotation.text.strip()
    return None


def _delimited(tex: str, display: bool) -> str:
    return f"\\[{tex}\\]" if display else f"\\({tex}\\)"


def _replace_with_text(element: Any, text: str) -> None:
    """Put ``text`` where ``element`` was, its tail kept."""

    parent = element.getparent()
    if parent is None:
        return
    joined = text + (element.tail or "")
    previous = element.getprevious()
    if previous is not None:
        previous.tail = (previous.tail or "") + joined
    else:
        parent.text = (parent.text or "") + joined
    parent.remove(element)


def _remove(element: Any) -> None:
    """Remove ``element`` and everything in it, keeping its tail (the text after it belongs to its parent)."""

    if element.getparent() is not None:
        _replace_with_text(element, "")


def _squeeze(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def _letters(text: str) -> str:
    return re.sub(r"\W+", "", text or "")


__all__ = [
    "OLD_WEB_PAGE_EXTRACTOR_VERSION",
    "PAGE_FURNITURE",
    "WEB_PAGE_EXTRACTOR_VERSION",
    "display_formulas",
    "page_markdown",
    "prepare_page",
    "readable_markdown",
]
