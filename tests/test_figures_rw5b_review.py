"""RW5b Codex review fixes (docs/reviews/reader-rw5b-codex-review.md).

F2: a figure of a block is reused whatever offered it, and across the
panels switch when it can be drawn now. F4: a figure using a panel kind
that is switched off is not revised. F5: with the panels off, a chain shows
its newest version that can still be drawn. Fakes only: no model is called.
"""

from __future__ import annotations

import json
import re

import pytest

from learnloop.figures import routes as R
from learnloop.figures import service as FS
from learnloop.source_retrieval import library_ask as LA
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from tests.figure_fixtures import EXTRACTION, AuthorFake, build, call, context, rows, set_config
from tests.figure_panels_corpus import gradient_field
from tests.test_figure_offers import ExplorableOrganizer, _ask, _vault


def _panels(paths, on: bool) -> None:
    """Flip ``figures.advanced_panels_enabled`` (set_config appends, and a
    TOML key may be set only once)."""

    config = paths.root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    if "advanced_panels_enabled = " in text:
        config.write_text(re.sub(r"advanced_panels_enabled = (true|false)",
                                 f"advanced_panels_enabled = {'true' if on else 'false'}", text), encoding="utf-8")
    else:
        set_config(paths, "figures", advanced_panels_enabled=on)


def _offered_library(paths, repository) -> str:
    ask_id = _ask(repository)
    LA.organize(load_vault(paths.root), repository, ask_id, client=ExplorableOrganizer())
    return ask_id


# --- F2: one figure per block, whatever offered it -------------------------------------------------

def test_a_block_built_from_a_selection_is_reused_when_a_library_offer_names_it(tmp_path):
    paths, repository = _vault(tmp_path)
    ask_id = _offered_library(paths, repository)
    author = AuthorFake()
    ctx = context(paths.root, author=author)
    first = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p3"]})["figure"]
    assert first["origin"] == "selection" and author.calls == 1
    again = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p3"], "origin": "library", "offerRef": ask_id})
    assert again["reused"] is True and again["figure"]["figureId"] == first["figureId"]
    assert author.calls == 1
    assert len(rows(repository, "interactive_figures")) == 1
    # Under the passage: one figure, not one per origin.
    assert len(call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]) == 1


def test_the_reuse_key_never_names_the_origin_and_keeps_rw5as_keys():
    request = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"], origin="tutor")
    selection = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"], origin="selection")
    source = FS.SourceContext(passage=[{"span_id": "p3", "text": "f"}], around=[], figure_span=None)
    assert FS.request_hash(request, source, None) == FS.request_hash(selection, source, None)
    assert FS.REUSE_ORIGIN == "selection"


def test_a_figure_built_before_the_panels_came_on_is_reused_with_them_on(tmp_path):
    paths, repository = _vault(tmp_path, advanced_panels_enabled=False)
    author = AuthorFake()
    first = build(context(paths.root, author=author), {"extractionId": EXTRACTION, "spanIds": ["p3"]})["figure"]
    assert rows(repository, "interactive_figures")[0]["prompt_version"] == R.AUTHOR_PROMPT_VERSION
    _panels(paths, True)
    again = build(context(paths.root, author=author), {"extractionId": EXTRACTION, "spanIds": ["p3"]})
    assert again["reused"] is True and again["figure"]["figureId"] == first["figureId"]
    assert author.calls == 1


def test_a_figure_that_cant_be_drawn_now_is_not_reused_across_the_switch(tmp_path):
    paths, repository = _vault(tmp_path)
    build(context(paths.root, author=AuthorFake([gradient_field()])), {"extractionId": EXTRACTION, "spanIds": ["p2"]})
    _panels(paths, False)
    author = AuthorFake()
    again = build(context(paths.root, author=author), {"extractionId": EXTRACTION, "spanIds": ["p2"]})
    assert again["reused"] is False and author.calls == 1
    assert again["figure"]["specJson"] is not None


def test_another_prompts_cant_draw_verdict_is_not_reused(tmp_path):
    paths, repository = _vault(tmp_path, advanced_panels_enabled=False)
    first = build(context(paths.root, author=AuthorFake([("unsupported", "a vector field")])),
                  {"extractionId": EXTRACTION, "spanIds": ["p2"]})["figure"]
    assert first["verification"] == "unsupported"
    _panels(paths, True)
    author = AuthorFake([gradient_field()])
    again = build(context(paths.root, author=author), {"extractionId": EXTRACTION, "spanIds": ["p2"]})
    assert author.calls == 1 and again["figure"]["verification"] == "illustrative"


# --- F4: no revision of a figure whose panels are switched off --------------------------------------

def test_a_figure_using_a_switched_off_panel_is_not_revised(tmp_path):
    paths, repository = _vault(tmp_path)
    shown = build(context(paths.root, author=AuthorFake([gradient_field()])),
                  {"extractionId": EXTRACTION, "spanIds": ["p2"]})["figure"]
    _panels(paths, False)
    author = AuthorFake()
    ctx = context(paths.root, author=author)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_revise", {"figureId": shown["figureId"], "note": "show the minimum"})
    assert caught.value.code == "advanced_disabled"
    assert author.calls == 0
    assert len(rows(repository, "interactive_figures")) == 1


# --- F5: the newest version that can still be drawn -----------------------------------------------

def test_with_the_panels_off_a_chain_shows_its_newest_drawable_version(tmp_path):
    paths, repository = _vault(tmp_path)
    author = AuthorFake()  # the flagship function plot (RW5a's kinds) first
    ctx = context(paths.root, author=author)
    first = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p3"]})["figure"]
    author.answers = [gradient_field()]
    revised = build(ctx, {"figureId": first["figureId"], "note": "as a field"}, rpc="reader.figure_revise")["figure"]
    assert json.loads(revised["specJson"])["panels"][0]["kind"] == "vector_field_2d"
    on = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert [figure["figureId"] for figure in on] == [revised["figureId"]]
    _panels(paths, False)
    off = call(context(paths.root, author=AuthorFake()), "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert [(figure["figureId"], figure["verification"]) for figure in off] == [(first["figureId"], "illustrative")]
    assert off[0]["specJson"] is not None and off[0]["versions"] == 2
