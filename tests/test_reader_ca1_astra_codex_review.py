"""Reader CA1, the Codex review of the Astra batch fixes (F1-F3).

* F1 (High): a free crop needs an affirmative stem-only boundary. A block
  with words after the statement ("Compute 2+2. The answer is 4.") gives
  no free crop, whatever the leak matcher says (it ignores a lone digit and
  a short word), and neither does an owned block that shares no words with
  the statement (nothing says it is the stem).
* F2 (High): a single-exercise import keeps the figure the author calls
  its stimulus, whether or not the statement echoes the figure's text, so
  a check on your own still shows the figure; a problem with no free crop
  keeps it too. One the author does not call stimulus is not (the Astra
  redesign: roles from the author's structured output, never from words;
  rewritten from the lexical rule these tests first pinned).
* F3 (Medium): a block the import's check names as the book's solution that
  also holds part of the statement is not dropped from the crop (a partial
  print): the whole crop is withheld, the original page still offered.

A real PDF is drawn here (no book text is committed); every model is a fake.
"""

from __future__ import annotations

import hashlib
import io

import pytest
from PIL import Image, ImageDraw

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.ingest.originals import store_original_bytes
from learnloop.reader.as_printed import FIGURE_LABEL, NO_CROP
from tests.test_reader_ca1_as_printed import (  # noqa: F401 - fixtures
    BLUE,
    GREEN,
    RED,
    _call,
    _image,
    _share,
    book,
    cold,
    warm,
)
from tests.test_reader_ca1_astra_fixes import _mark_every_block_owned, _owned
from tests.test_source_inventory import _persist

EXT = "ext_ca1_codex"
NOW_ISO = "2026-01-01T00:00:00Z"
#: (span, type, page, bbox, colour, text).
LAYOUT = (
    ("t1", "Text", 0, [72.0, 100.0, 540.0, 140.0], RED, "Exercise 5. Find the slope of the graph shown."),
    ("f1", "Figure", 0, [72.0, 150.0, 300.0, 330.0], GREEN, "A line through (0, 0) and (2, 4)."),
    ("m1", "Text", 0, [72.0, 400.0, 540.0, 440.0], BLUE, "Compute 2+2. The answer is 4."),
    ("y1", "Text", 0, [72.0, 460.0, 540.0, 500.0], BLUE, "Is 7 prime? Yes."),
    ("a1", "Text", 1, [72.0, 50.0, 540.0, 90.0], RED, "Exercise 6. (a) Compute 2+2."),
    ("b1", "Text", 1, [72.0, 100.0, 540.0, 140.0], RED, "(b) Compute 3+3. We get 6."),
    ("u1", "Text", 1, [72.0, 200.0, 540.0, 240.0], BLUE, "The sum is 4."),
)


def _seed(root, repository) -> None:
    pages = []
    for page in (0, 1):
        image = Image.new("RGB", (612, 792), "white")
        draw = ImageDraw.Draw(image)
        for _span, _kind, block_page, bbox, colour, _text in LAYOUT:
            if block_page == page:
                draw.rectangle(bbox, fill=colour)
        pages.append(image)
    out = io.BytesIO()
    pages[0].save(out, format="PDF", resolution=72.0, save_all=True, append_images=pages[1:])
    raw = out.getvalue()
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    store_original_bytes(root, digest, raw)
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, display_title, current_revision_id, "
            "reader_enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            ("src_cx", "pdf", "file:///nowhere/book.pdf", "Strang", "rev_cx", 1, NOW_ISO, NOW_ISO))
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            ("rev_cx", "src_cx", digest, None, NOW_ISO))
        connection.commit()
    blocks = [DocumentBlock.build(span_id=span, block_type=kind, text=text, ordinal=index, page=page, bbox=bbox,
                                  section_path=["6.1"])
              for index, (span, kind, page, bbox, _colour, text) in enumerate(LAYOUT, start=1)]
    unit = DocumentUnit(unit_id="u_cx", label="6.1", ordinal=0, semantic_hash="sha256:u_cx", page_start=0,
                        page_end=1, span_ids=[block.span_id for block in blocks])
    ir = DocumentIR(extractor="marker", extractor_version="1", units=[unit], blocks=blocks, assets=[],
                    health=ExtractionHealth())
    _persist(repository, ir, revision_id="rev_cx", extraction_id=EXT)


@pytest.fixture
def seeded(book):
    paths, ctx, repository = book
    _seed(paths.root, repository)
    return paths, ctx, repository


def _text(span: str) -> str:
    return next(text for name, _kind, _page, _bbox, _colour, text in LAYOUT if name == span)


def _import(paths, repository, spans: list[str], statement: str, answer: str, *,
            roles: dict[str, str] | None = None) -> str:
    """``roles``: the author's figure roles (the Astra redesign: a figure is
    the problem's only as a validated ``stimulus``)."""

    from learnloop.content.authoring import exercise_authoring as EX
    from learnloop.content.authoring.ai_contracts import ExerciseAuthoring, FigureRolePayload
    from tests.test_exercise_authoring import FakeClient, _item, _write_facet_registry

    _write_facet_registry(paths.root.parent)
    raw = {"nodes": [{"spanId": span, "quote": _text(span)} for span in spans]}
    claims = [FigureRolePayload(span_id=span, role=role) for span, role in (roles or {}).items()]
    client = FakeClient(ExerciseAuthoring(items=[_item(statement_md=statement, expected_answer_md=answer,
                                                       figure_roles=claims)]))
    (summary,) = EX.import_exercises(paths.root, repository, client, extraction_id=EXT, raw_selection=raw,
                                     source_id="src_cx")["items"]
    return summary["practice_item_id"]


def _view(ctx, item_id: str) -> dict:
    ctx.reload(maintenance=False)
    return _call(ctx, "practice.as_printed", {"practiceItemId": item_id, "render": True})


def _no_free_crop(view: dict, span: str) -> None:
    assert view["kind"] == "page" and view["crops"] == [] and view["notice"] == NO_CROP
    assert view["originalPage"]["extractionId"] == EXT and view["originalPage"]["spanId"] == span


# -- F1: an affirmative stem-only boundary -------------------------------------------------------------


@pytest.mark.parametrize(("span", "statement", "answer"), [
    ("m1", "Compute 2+2.", "4"),            # a lone digit: the leak matcher ignores it
    ("y1", "Is 7 prime?", "Yes"),           # a short word: the leak matcher ignores it too
])
def test_words_after_the_statement_in_its_block_give_no_free_crop(seeded, warm, span, statement, answer):
    from learnloop.tutor.tutor_qa import span_leaks_expected

    paths, ctx, repository = seeded
    # The leak matcher alone would call the block safe (the review's scenario).
    assert not span_leaks_expected(_text(span), answer)
    item_id = _import(paths, repository, [span], statement, answer)
    assert _owned(paths, item_id) == [True]
    _no_free_crop(_view(ctx, item_id), span)


def test_a_label_before_the_statement_still_crops(seeded, warm):
    """The affirmative case: the block's other words all precede the statement."""

    paths, ctx, repository = seeded
    item_id = _import(paths, repository, ["a1"], "(a) Compute 2+2.", "4")
    view = _view(ctx, item_id)
    assert [crop["spanIds"] for crop in view["crops"]] == [["a1"]]


def test_an_owned_block_sharing_no_words_with_the_statement_gives_no_free_crop(seeded, warm):
    """An item marked by the old rule (every selected block owned) with an
    unlabelled solution block: no lead, no role, no import check, and a lone
    digit the leak matcher ignores. Nothing says the block is the stem."""

    paths, ctx, repository = seeded
    item_id = _import(paths, repository, ["a1", "u1"], "(a) Compute 2+2.", "4")
    _mark_every_block_owned(paths, item_id)
    _no_free_crop(_view(ctx, item_id), "a1")


# -- F2: the stimulus figure of a single-exercise import -----------------------------------------------


def test_a_statement_that_names_but_does_not_echo_its_figure_keeps_it(seeded, warm):
    paths, ctx, repository = seeded
    item_id = _import(paths, repository, ["t1", "f1"], "Find the slope of the graph shown.", "2",
                      roles={"f1": "stimulus"})
    assert _owned(paths, item_id) == [True, True]
    view = _view(ctx, item_id)
    assert {span for crop in view["crops"] for span in crop["spanIds"]} == {"t1", "f1"}


def test_a_check_on_your_own_still_shows_the_figure_the_statement_names(seeded, cold):
    paths, ctx, repository = seeded
    item_id = _import(paths, repository, ["t1", "f1"], "Find the slope of the graph shown.", "2",
                      roles={"f1": "stimulus"})
    view = _view(ctx, item_id)
    assert view["kind"] == "figure" and view["label"] == FIGURE_LABEL and len(view["crops"]) == 1
    assert _share(_image(view["crops"][0]["image"]), GREEN) > 0.9


def test_a_paraphrased_statement_keeps_its_figure_for_a_check_on_your_own(seeded, cold):
    paths, ctx, repository = seeded
    item_id = _import(paths, repository, ["t1", "f1"], "What is the slope of that line?", "2",
                      roles={"f1": "stimulus"})
    assert _owned(paths, item_id) == [False, True]          # no text owned; the figure by its role
    view = _view(ctx, item_id)
    assert view["kind"] == "figure" and _share(_image(view["crops"][0]["image"]), GREEN) > 0.9


def test_a_figure_the_statement_does_not_refer_to_is_not_its_stimulus(seeded, cold):
    """Codex re-review F5: selected is not enough. The author did not call
    the figure beside "Compute 2+2." its stimulus, so it is not shown."""

    paths, ctx, repository = seeded
    item_id = _import(paths, repository, ["m1", "f1"], "Compute 2+2.", "4")
    assert _view(ctx, item_id)["kind"] == "none"


def test_a_paraphrase_shows_no_free_crop_of_its_figure_alone(seeded, warm):
    paths, ctx, repository = seeded
    item_id = _import(paths, repository, ["t1", "f1"], "What is the slope of that line?", "2")
    _no_free_crop(_view(ctx, item_id), "t1")


# -- F3: a named solution block that also holds part of the statement -----------------------------------


def test_a_named_solution_block_holding_part_of_the_statement_withholds_the_whole_crop(seeded, warm):
    from learnloop.content.authoring import source_exercise_import as SEI
    from learnloop.db.stores.source_service import update_import

    paths, ctx, repository = seeded
    item_id = _import(paths, repository, ["a1", "b1"], "(a) Compute 2+2. (b) Compute 3+3.", "4 and 6")
    assert _owned(paths, item_id) == [True, True]
    (row,) = SEI.record_reader_import(paths.root, repository, {"items": [{"practice_item_id": item_id}]},
                                      extraction_id=EXT, span_ids=["a1", "b1"], source_id="src_cx",
                                      revision_id="rev_cx")
    with repository.connection() as connection:
        update_import(connection, row["import_id"], updated_at=NOW_ISO,
                      verification={"book_solution": {"span_ids": ["b1"], "page": 1}})
        connection.commit()
    view = _view(ctx, item_id)
    # Never a crop of (a) alone: part (b) is in the block that also holds the answer.
    _no_free_crop(view, "a1")
