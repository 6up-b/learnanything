"""UX-2 (UX journey audit, walks student-1, beginner-1, retainer-1, phone-2): a source's own TeX macros.

The sample chapter defines 61 macros with ``\\newcommand`` in a hidden element; the extraction keeps the
formulas and drops the definitions, so the Reader showed ``\\vvec`` as a red raw command and ``\\real`` as
KaTeX's own ℜ. The definitions are now read from the stored original and handed to the renderers beside the
blocks. Nothing stored changes: the pins below were taken from this production path before the change.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.db.connection import connect
from learnloop.reader.source_macros import (
    MAX_BODY_LENGTH,
    MAX_MACROS,
    MAX_NAME_LENGTH,
    macros_from_original,
    parse_tex_macros,
)
from learnloop_sidecar.context import SidecarContext
from tests.ux_phase1_add_source_helpers import _draining_ctx, call
from tests.ux_phase1_support import CLOCK, fresh_library, grant_consent
from tests.web_page_reading_helpers import old_web_reading_services

SAMPLE = Path(__file__).resolve().parents[1] / "samples" / "understanding-linear-algebra-symmetric-matrices-and-variance.html"

# Taken from the production path (add_source -> html extraction -> blocks -> reader.render_view) before UX-2.
# The run's request and result hashes key on the revision's id, new at each import, so they are not pinned;
# the blocks' own content hashes, and the render view's hash over them, are. Since UX-11 a new read of a web
# page is extraction version 3: these pins are the sample as a library read it before (version 2), which is
# what ``added_sample`` holds (``tests/web_page_reading_helpers.py``).
EXTRACTOR = ("html", "2")
BLOCK_COUNT = 59
#: sha256 over "span_id<TAB>content_hash" lines in reading order.
BLOCKS_DIGEST = "f03ceb9f3682844a26e8a9d418be1118a5c01335fe614a5e35a2706fb7769202"
#: One block that uses the macros, by its span and content hash.
MACRO_BLOCK = ("s5", "sha256:57f99b7f4b56d3b31564c59405180f10c59988a3bfd208ad95482cf68d46b09d")
RENDER_VIEW_CONTENT_HASH = "sha256:4d153455175b0d1ba1437e93a952d530b321c38b59534e00287993f56cb7fcbd"


@pytest.fixture
def added_sample(tmp_path):
    """The sample in a library that read it before UX-11, opened by the current code."""

    root = fresh_library(tmp_path)
    grant_consent(root)
    page = tmp_path / SAMPLE.name
    page.write_bytes(SAMPLE.read_bytes())
    before = SidecarContext()
    before.load(root)
    before.ingest_jobs.bind(before.repository, root, background=False, clock=CLOCK,
                            services=old_web_reading_services(SAMPLE.name))
    source_id = call(before, "add_source", {"sources": [str(page)]})["items"][0]["sourceId"]
    ctx = _draining_ctx(root)
    return root, ctx, source_id, resolve_extraction_id(ctx.repository, source_id)


def test_ux2_a_new_read_of_the_sample_carries_the_pages_macros_and_stores_none_of_them(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    page = tmp_path / SAMPLE.name
    page.write_bytes(SAMPLE.read_bytes())
    ctx = _draining_ctx(root)
    source_id = call(ctx, "add_source", {"sources": [str(page)]})["items"][0]["sourceId"]
    extraction_id = resolve_extraction_id(ctx.repository, source_id)
    run, rows = _stored_blocks(ctx, extraction_id)
    assert run == ("html", "3")
    assert any("\\vvec" in text for _, _, text in rows)
    assert not any("\\newcommand" in text for _, _, text in rows)
    view = call(ctx, "reader.render_view", {"extractionId": extraction_id})
    assert view["mathMacros"]["\\vvec"] == "{\\mathbf v}" and len(view["mathMacros"]) == 61


def _stored_blocks(ctx, extraction_id):
    with connect(ctx.repository.sqlite_path) as connection:
        run = connection.execute(
            "SELECT extractor, extractor_version FROM source_extraction_runs WHERE id = ?",
            (extraction_id,),
        ).fetchone()
        rows = connection.execute(
            "SELECT span_id, content_hash, text FROM source_document_blocks WHERE extraction_id = ? ORDER BY ordinal",
            (extraction_id,),
        ).fetchall()
    return tuple(run), rows


def test_ux2_the_sample_is_stored_as_before_and_its_reading_carries_the_pages_macros(added_sample):
    _root, ctx, _source_id, extraction_id = added_sample

    run, rows = _stored_blocks(ctx, extraction_id)
    # What is stored and hashed is what it was: the definitions are not written into any block.
    assert run == EXTRACTOR
    assert len(rows) == BLOCK_COUNT
    assert hashlib.sha256("\n".join(f"{span}\t{digest}" for span, digest, _ in rows).encode()).hexdigest() == BLOCKS_DIGEST
    assert any("\\vvec" in text for _, _, text in rows)
    assert any((span, digest) == MACRO_BLOCK and "\\real" in text for span, digest, text in rows)
    assert not any("\\newcommand" in text for _, _, text in rows)

    view = call(ctx, "reader.render_view", {"extractionId": extraction_id})
    assert view["contentHash"] == RENDER_VIEW_CONTENT_HASH
    assert [block["markdown"] for block in view["blocks"]] == [text for _, _, text in rows]

    macros = view["mathMacros"]
    assert macros["\\vvec"] == "{\\mathbf v}"
    assert macros["\\uvec"] == "{\\mathbf u}"
    # The book's ℝ, not KaTeX's built-in \real (ℜ).
    assert macros["\\real"] == "{\\mathbb R}"
    # Entities are decoded, as the page's MathJax read them.
    assert macros["\\amp"] == "&"
    assert macros["\\lt"] == "<"
    assert macros["\\twovec"] == "\\left[\\begin{array}{r}#1 \\\\ #2\n\\end{array}\\right]"
    # \row is defined, then redefined: one entry, the later body.
    assert macros["\\row"] == "\\text{Row}"
    # 62 definitions (61 \newcommand, one \renewcommand of \row), 61 names; within every bound. (The file's
    # other two "newcommand" strings name MathJax's package in its configuration script: not definitions.)
    assert len(macros) == 61
    assert len(macros) <= MAX_MACROS
    assert all(len(name) - 1 <= MAX_NAME_LENGTH and len(body) <= MAX_BODY_LENGTH for name, body in macros.items())


def test_ux2_a_source_added_before_reads_its_macros_from_the_stored_original_without_a_new_reading(added_sample):
    root, ctx, source_id, extraction_id = added_sample
    # Nothing about macros is stored at ingest: a source added before this change is the same rows,
    # and its reading gets the macros when it is opened, read from canonical-sources/raw/.
    view = call(ctx, "reader.render_view", {"extractionId": extraction_id})
    assert view["mathMacros"]["\\vvec"] == "{\\mathbf v}"
    with connect(ctx.repository.sqlite_path) as connection:
        runs = connection.execute(
            "SELECT COUNT(*) FROM source_extraction_runs r JOIN source_revisions v ON v.id = r.revision_id WHERE v.source_id = ?",
            (source_id,),
        ).fetchone()[0]
    assert runs == 1

    # Without its stored original (a pre-store revision), the reading opens as before, with no macros.
    for stored in (root / "canonical-sources" / "raw").iterdir():
        stored.unlink()
    from learnloop.reader import source_macros

    source_macros._cached_macros.cache_clear()
    view = call(ctx, "reader.render_view", {"extractionId": extraction_id})
    assert "mathMacros" not in view
    assert view["contentHash"] == RENDER_VIEW_CONTENT_HASH


def test_ux2_only_plain_definitions_are_read():
    text = r"""
    \newcommand{\vvec}{{\mathbf v}}
    \newcommand\bare{x}
    \newcommand*{\starred}[1]{#1^2}
    \renewcommand{\vvec}{\mathbf{v}}
    \providecommand{\vvec}{ignored}
    \def\pair#1#2{(#1,#2)}
    \def\dotted#1.{#1}
    \newcommand{\opt}[2][0]{#1+#2}
    \newcommand{\toomany}[1]{#1#2}
    \newcommand{\esc}{\{\}}
    \definecolor{shade}{gray}{0.9}
    """
    assert parse_tex_macros(text) == {
        "\\vvec": "\\mathbf{v}",
        "\\bare": "x",
        "\\starred": "#1^2",
        "\\pair": "(#1,#2)",
        "\\esc": "\\{\\}",
    }


@pytest.mark.parametrize(
    "body",
    [
        r"\input{/etc/passwd}",
        r"\include{chapter}",
        r"\catcode`\@=11",
        r"\csname foo\endcsname",
        r"\def\inner{x}",
        r"\gdef\leak{x}",
        r"\newcommand{\inner}{x}",
        r"\expandafter\x\y",
        r"\href{https://example.com}{x}",
        r"\htmlClass{x}{y}",
        r"\write18{rm -rf}",
    ],
)
def test_ux2_a_body_that_could_define_include_or_reach_out_is_dropped(body):
    assert parse_tex_macros("\\newcommand{\\bad}{" + body + "}\\newcommand{\\good}{g}") == {"\\good": "g"}


def test_ux2_a_recursive_macro_is_kept_as_text_and_left_to_katexs_expansion_limit():
    # Never expanded here: the table holds the body as written, and parsing returns at once.
    assert parse_tex_macros(r"\newcommand{\loop}{\loop\loop} \def\again{\again}") == {
        "\\loop": "\\loop\\loop",
        "\\again": "\\again",
    }


def test_ux2_an_oversized_table_is_cut_at_the_bounds():
    many = "".join(f"\\newcommand{{\\m{chr(97 + i % 26)}{chr(97 + i // 26 % 26)}{chr(97 + i // 676)}}}{{{i}}}" for i in range(MAX_MACROS + 50))
    table = parse_tex_macros(many)
    assert len(table) == MAX_MACROS

    long_name = "\\newcommand{\\" + "a" * (MAX_NAME_LENGTH + 1) + "}{x}\\newcommand{\\ok}{y}"
    assert parse_tex_macros(long_name) == {"\\ok": "y"}

    long_body = "\\newcommand{\\big}{" + "x" * (MAX_BODY_LENGTH + 1) + "}\\newcommand{\\ok}{y}"
    assert parse_tex_macros(long_body) == {"\\ok": "y"}

    # An unclosed body never scans the rest of the page.
    unclosed = "\\newcommand{\\open}{" + "{" * 10 + "x" * 100_000
    assert parse_tex_macros(unclosed) == {}


def test_ux2_scripts_and_binaries_give_no_macros():
    page = (
        b"<!doctype html><html><head><script>var s = '\\\\newcommand{\\\\evil}{x}';</script></head>"
        b"<body><div style='display:none'>\\(\\newcommand{\\hidden}{h}\\)</div><p>\\(\\hidden\\)</p></body></html>"
    )
    assert macros_from_original(page) == {"\\hidden": "h"}
    assert macros_from_original(b"%PDF-1.7 \\newcommand{\\x}{y}") == {}
    assert macros_from_original(b"\x00\x01\\newcommand{\\x}{y}") == {}
    assert macros_from_original(b"$$\\newcommand{\\R}{\\mathbb R}$$ text") == {"\\R": "\\mathbb R"}


def test_ux2_the_second_pane_gets_its_own_books_macros(tmp_path):
    from learnloop.ingest.originals import store_original_bytes
    from tests.reading_path_fixtures import call as rpc
    from tests.reading_path_fixtures import context
    from tests.section_coverage_fixtures import build_coverage_vault

    # No held-out unit on this book: a protected book's pane carries none (tests/test_ux2_macros_protection.py).
    paths, repository = build_coverage_vault(tmp_path / "vault", held_out=False)
    run = repository.get_extraction_run("ext_lay")
    revision = repository.get_source_revision(run["revision_id"])
    # The other book's original, kept under its revision's digest as an import keeps it.
    store_original_bytes(paths.root, revision["asset_hash"],
                         b"<!doctype html><div hidden>\\(\\newcommand{\\real}{{\\mathbb R}}\\)</div><p>x</p>")
    section = rpc(context(paths.root, coverage_inline=True), "reader.side_by_side_section",
                  {"extraction_id": "ext_lay", "section_id": "lay_char"})["section"]
    assert section["mathMacros"] == {"\\real": "{\\mathbb R}"}
