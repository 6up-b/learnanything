"""Reader RW5c, Astra review A1: a candidate comes only from a block the Reader displays.

The page drops whole blocks before Markdown sees them (``readerBlockPolicy.json``, which ``ReaderScreen`` and
:mod:`learnloop.reader.source_render_views` both read), so a check that reads them could certify what the page never shows.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest

from learnloop.content.authoring import pf_sandbox
from learnloop.figures import source_check as SC
from learnloop.figures import spec as S
from learnloop.reader import source_render_views as RV
from learnloop.vault.loader import load_vault
from tests.rw5c_fixtures import EXTRACTION, build_check_vault, plot

sandboxed = pytest.mark.skipif(not pf_sandbox.sandbox_available(), reason="needs bubblewrap")
_POLICY = json.loads(RV.BLOCK_POLICY_PATH.read_text(encoding="utf-8"))


def _check(book: tuple[Any, Any], spec: dict[str, Any], *spans: str) -> SC.Check:
    vault, repository = book
    return SC.check_figure(vault, repository, S.parse_spec(spec), spans=[(EXTRACTION, span, span) for span in spans],
                           grounding="anchor")


@sandboxed
@pytest.mark.parametrize("furniture", ["PageHeader", "PageFooter", "TableOfContents"])
def test_an_equation_in_furniture_never_certifies_a_curve_beside_a_page_showing_another(tmp_path, furniture):
    """A1: the header says f(x)=x, the page shows only f(x)=2x, and a figure of x was "checked" with the header as its page."""

    paths, repository = build_check_vault(tmp_path / "vault", [
        ("head", furniture, r"The identity $f(x)=x$"), ("body", "Text", r"Now consider $f(x)=2x$.")])
    book = (load_vault(paths.root), repository)
    hidden = _check(book, plot("x", low=0.0, high=1.0), "head", "body")
    assert hidden.outcome != SC.CHECKED and not hidden.book_elements
    shown = _check(book, plot("2*x", low=0.0, high=1.0), "head", "body")
    assert shown.outcome == SC.CHECKED
    assert {element["source"]["span_id"] for element in shown.book_elements} == {"body"}


def _candidates(tmp_path: Any, block_type: str, *, uri: str | None = None) -> tuple[list[Any], dict[str, int]]:
    paths, repository = build_check_vault(tmp_path / "vault", [("a", block_type, r"Here $f(x)=x$.")])
    if uri is not None:
        with repository.connection() as connection:
            connection.execute("UPDATE source_artifacts SET canonical_uri = ? WHERE id = 'src_math'", (uri,))
            connection.commit()
    return SC.read_candidates(load_vault(paths.root), repository, [(EXTRACTION, "a", "a")])


@pytest.mark.parametrize("block_type", _POLICY["markdown"])
def test_every_type_the_page_gives_its_markdown_holds_candidates(tmp_path, block_type):
    candidates, reasons = _candidates(tmp_path, block_type)
    assert [candidate.relation.latex for candidate in candidates] == ["f(x)=x"] and not reasons


@pytest.mark.parametrize("block_type", [*_POLICY["furniture"], "ATypeNobodyMet", "text", ""])
def test_furniture_and_a_type_nobody_met_hold_none(tmp_path, block_type):
    """Fail closed: the page shows a new type through its filter, and no check vouches for it until it is listed."""

    candidates, reasons = _candidates(tmp_path, block_type)
    assert not candidates and reasons == {"block_not_shown": 1}


def test_a_furniture_block_with_no_math_refuses_nothing(tmp_path):
    paths, repository = build_check_vault(tmp_path / "vault", [("a", "PageHeader", "Chapter 5")])
    assert SC.read_candidates(load_vault(paths.root), repository, [(EXTRACTION, "a", "a")]) == ([], {})


@pytest.mark.parametrize("uri", ["https://www.youtube.com/watch?v=abc", "https://youtu.be/abc", "https://m.youtube.com/shorts/abc"])
def test_a_source_on_the_watch_surface_holds_none(tmp_path, uri):
    """YouTubeWatchPanel shows each cue's text as it is, with no MarkdownMath: $x^ab$ reads as x^a b under text showing x^ab."""

    candidates, reasons = _candidates(tmp_path, "Caption", uri=uri)
    assert not candidates and reasons == {"block_not_shown": 1}


def test_a_caption_of_a_book_is_read_as_the_page_shows_it(tmp_path):
    candidates, _reasons = _candidates(tmp_path, "Caption", uri="file:///a/youtube.pdf")
    assert len(candidates) == 1


def test_a_source_nobody_can_find_or_an_unreadable_policy_shows_nothing(tmp_path, monkeypatch):
    paths, repository = build_check_vault(tmp_path / "vault", [("a", "Text", r"$f(x)=x$")])
    vault = load_vault(paths.root)
    monkeypatch.setattr(repository, "get_source_artifact", lambda _source: None)
    assert SC.read_candidates(vault, repository, [(EXTRACTION, "a", "a")]) == ([], {"block_not_shown": 1})
    monkeypatch.undo()
    monkeypatch.setattr(RV, "BLOCK_POLICY_PATH", tmp_path / "missing.json")
    RV._block_policy.cache_clear()
    try:
        assert not RV.page_renders_block_type("Text") and not RV.page_renders_source("book.pdf")
    finally:
        monkeypatch.undo()
        RV._block_policy.cache_clear()


def test_every_type_an_extractor_writes_is_classified():
    """A type added to an extractor is listed here too, so the page's new block isn't quietly unreadable."""

    from learnloop.ingest.extractors import glm_ocr

    known = {*_POLICY["furniture"], *_POLICY["markdown"]}
    written = {*glm_ocr._BLOCK_TYPES.values(), "Text", "SectionHeader", "Caption", "Code", "Equation", "Footnote"}
    # Marker's own, by hand (the pdf extra isn't in this gate's environment), less its layout-only Line, Span, Char, Page and Document.
    marker = {"FigureGroup", "TableGroup", "ListGroup", "PictureGroup", "Caption", "Code", "Figure", "Footnote", "Form",
              "Equation", "Handwriting", "TextInlineMath", "ListItem", "PageFooter", "PageHeader", "Picture", "SectionHeader",
              "Table", "Text", "TableOfContents", "ComplexRegion", "TableCell", "Reference"}
    assert written | marker <= known
    assert not set(_POLICY["furniture"]) & set(_POLICY["markdown"])


def test_the_page_reads_this_policy_and_a_change_to_it_needs_a_certification_bump():
    screen = (RV.BLOCK_POLICY_PATH.parents[1] / "screens" / "ReaderScreen.tsx").read_text(encoding="utf-8")
    module = (RV.BLOCK_POLICY_PATH.parent / "readerBlockPolicy.ts").read_text(encoding="utf-8")
    assert "readerDisplaysBlock(b.blockType)" in screen and '"PageHeader"' not in screen
    assert 'from "./readerBlockPolicy.json"' in module
    # Another policy can make a stored candidate one the page doesn't show: bump CERTIFICATION_VERSION with it, then this tuple.
    assert (SC.CERTIFICATION_VERSION, hashlib.sha256(RV.BLOCK_POLICY_PATH.read_bytes()).hexdigest()[:12]) == (7, "a6f23ef6343f")
