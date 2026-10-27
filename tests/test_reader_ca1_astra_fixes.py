"""Reader CA1, the Astra batch review's High and the CA1 polish (owner, 2026-10-26).

The owner: "viewing the original exam page picture ocr is fine to make sure
theres no latex errors in the exam question, but i would hope that crop
excludes the solution." So:

* a single-exercise import owns the blocks its anchored statement covers,
  never every block selected: a selection of a problem and its separate
  solution block crops only the problem (the Astra scenario);
* at read time a stored mark is never trusted over a solution: an import
  marked by the old rule (every block owned) crops only the problem too, and
  so does one whose import check found the book's solution blocks;
* a block holding the stem and its solution together leaves no free crop
  (``NO_CROP``), and the original page is still offered (one hint before
  Submit, unchanged);
* the header names the book by its learner title when it has no display
  title, and an empty exercise label is no label.

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
from learnloop.reader.as_printed import NO_CROP
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.test_reader_ca1_as_printed import (  # noqa: F401 - fixtures
    BLUE,
    GREEN,
    ITEM,
    RED,
    _call,
    _image,
    _share,
    book,
    warm,
)
from tests.test_source_inventory import _persist

SOL = "ext_ca1_solution"
NOW_ISO = "2026-01-01T00:00:00Z"
#: (span, page, bbox, colour, text): a problem, its solution in a block of its
#: own just below, and on page 1 a block holding a stem and its solution.
SOL_LAYOUT = (
    ("p1", 0, [72.0, 100.0, 540.0, 140.0], RED, "Exercise 3. Compute 2+2."),
    ("q1", 0, [72.0, 150.0, 540.0, 190.0], BLUE, "Solution. The sum is 4."),
    ("m1", 1, [72.0, 50.0, 540.0, 90.0], GREEN, "Exercise 4. Compute 3+3. Solution: 3+3 = 6."),
)


def _seed(root, repository, *, display_title: str | None = "Strang") -> None:
    pages = []
    for page in (0, 1):
        image = Image.new("RGB", (612, 792), "white")
        draw = ImageDraw.Draw(image)
        for _span, block_page, bbox, colour, _text in SOL_LAYOUT:
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
            ("src_sol", "pdf", "file:///nowhere/linear_algebra_done_right.pdf", display_title, "rev_sol", 1,
             NOW_ISO, NOW_ISO))
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            ("rev_sol", "src_sol", digest, None, NOW_ISO))
        connection.commit()
    blocks = [DocumentBlock.build(span_id=span, block_type="Text", text=text, ordinal=index, page=page, bbox=bbox,
                                  section_path=["6.1"])
              for index, (span, page, bbox, _colour, text) in enumerate(SOL_LAYOUT, start=1)]
    unit = DocumentUnit(unit_id="u_sol", label="6.1", ordinal=0, semantic_hash="sha256:u_sol", page_start=0,
                        page_end=1, span_ids=[block.span_id for block in blocks])
    ir = DocumentIR(extractor="marker", extractor_version="1", units=[unit], blocks=blocks, assets=[],
                    health=ExtractionHealth())
    _persist(repository, ir, revision_id="rev_sol", extraction_id=SOL)


def _import(paths, repository, nodes: list[tuple[str, str]], statements: list[str], **item) -> list[str]:
    from learnloop.content.authoring import exercise_authoring as EX
    from learnloop.content.authoring.ai_contracts import ExerciseAuthoring
    from tests.test_exercise_authoring import FakeClient, _item, _write_facet_registry

    _write_facet_registry(paths.root.parent)
    raw = {"nodes": [{"spanId": span, "quote": quote} for span, quote in nodes]}
    client = FakeClient(ExerciseAuthoring(items=[_item(statement_md=statement, title=f"Exercise {index}", **item)
                                                 for index, statement in enumerate(statements, start=3)]))
    result = EX.import_exercises(paths.root, repository, client, extraction_id=SOL, raw_selection=raw,
                                 source_id="src_sol")
    return [summary["practice_item_id"] for summary in result["items"]]


@pytest.fixture
def solved(book):
    paths, ctx, repository = book
    _seed(paths.root, repository)
    return paths, ctx, repository


def _view(ctx, item_id: str) -> dict:
    ctx.reload(maintenance=False)
    return _call(ctx, "practice.as_printed", {"practiceItemId": item_id, "render": True})


def _owned(paths, item_id: str) -> list:
    refs = load_vault(paths.root).practice_items[item_id].provenance.source_refs
    return [ref.model_extra.get("owned") for ref in refs]


# -- (A) the Astra scenario: a single-item import of a problem and its separate solution -------------


def test_a_single_item_import_owns_only_its_statements_block_and_crops_only_the_problem(solved, warm):
    paths, ctx, repository = solved
    (item_id,) = _import(paths, repository, [("p1", "Exercise 3. Compute 2+2."), ("q1", "Solution. The sum is 4.")],
                         ["Compute 2+2."], expected_answer_md="4")
    # Every block stays a source ref (the selection is the provenance); only the problem's is owned.
    assert _owned(paths, item_id) == [True, False]
    view = _view(ctx, item_id)
    assert view["kind"] == "page" and [crop["spanIds"] for crop in view["crops"]] == [["p1"]]
    image = _image(view["crops"][0]["image"])
    assert _share(image, RED) > 0.9 and _share(image, BLUE) == 0            # none of the solution
    # The original page is still offered, outlining the problem's block only.
    assert view["originalPage"]["spanId"] == "p1" and view["originalPage"]["outlineSpanIds"] == ["p1"]


def test_a_paraphrased_single_statement_owns_nothing_and_offers_only_the_charged_page(solved, warm):
    paths, ctx, repository = solved
    (item_id,) = _import(paths, repository, [("p1", "Exercise 3. Compute 2+2."), ("q1", "Solution. The sum is 4.")],
                         ["Add two and two."], expected_answer_md="4")
    assert _owned(paths, item_id) == [False, False]
    view = _view(ctx, item_id)
    assert view["kind"] == "page" and view["crops"] == [] and view["notice"] == NO_CROP
    assert view["originalPage"]["extractionId"] == SOL


def _mark_every_block_owned(paths, item_id: str) -> None:
    """The rule before this fix: a single-item import marked every block it was given."""

    path = next(paths.root.rglob(f"{item_id}.yaml"))
    payload = read_yaml(path)
    for ref in payload["provenance"]["source_refs"]:
        ref["owned"] = True
    write_yaml(path, payload)


def test_an_item_marked_by_the_old_rule_never_crops_its_solution_block(solved, warm):
    paths, ctx, repository = solved
    (item_id,) = _import(paths, repository, [("p1", "Exercise 3. Compute 2+2."), ("q1", "Solution. The sum is 4.")],
                         ["Compute 2+2."], expected_answer_md="4")
    _mark_every_block_owned(paths, item_id)
    assert _owned(paths, item_id) == [True, True]
    view = _view(ctx, item_id)
    assert [crop["spanIds"] for crop in view["crops"]] == [["p1"]]
    assert _share(_image(view["crops"][0]["image"]), BLUE) == 0
    assert view["originalPage"]["outlineSpanIds"] == ["p1"]


def test_a_block_on_the_imports_book_solution_spans_is_never_cropped(solved, warm):
    """The import's check found the book's solution blocks (its row's
    ``verification.book_solution``): those are never part of the free crop,
    even with no solution lead of their own."""

    from learnloop.content.authoring import source_exercise_import as SEI
    from learnloop.db.stores.source_service import update_import

    paths, ctx, repository = solved
    (item_id,) = _import(paths, repository, [("p1", "Exercise 3. Compute 2+2."), ("q1", "Solution. The sum is 4.")],
                         ["Compute 2+2."], expected_answer_md="4")
    _mark_every_block_owned(paths, item_id)
    # Without the lead, only the import's record says q1 is the solution.
    with repository.connection() as connection:
        connection.execute("UPDATE source_document_blocks SET text='The sum is four.', role_hint=NULL "
                           "WHERE span_id='q1'")
        connection.commit()
    (row,) = SEI.record_reader_import(paths.root, repository, {"items": [{"practice_item_id": item_id}]},
                                      extraction_id=SOL, span_ids=["p1", "q1"], source_id="src_sol",
                                      revision_id="rev_sol")
    with repository.connection() as connection:
        update_import(connection, row["import_id"], updated_at=NOW_ISO,
                      verification={"book_solution": {"span_ids": ["q1"], "page": 0}})
        connection.commit()
    view = _view(ctx, item_id)
    assert [crop["spanIds"] for crop in view["crops"]] == [["p1"]]


# -- (A) a block that merges the stem and its solution: no free crop, the page still offered -----------


def test_a_block_holding_the_stem_and_its_solution_gives_no_crop_and_keeps_the_page(solved, warm):
    paths, ctx, repository = solved
    (item_id,) = _import(paths, repository, [("m1", "Exercise 4. Compute 3+3. Solution: 3+3 = 6.")],
                         ["Compute 3+3."], expected_answer_md="6")
    assert _owned(paths, item_id) == [True]          # the statement's block, which also holds its solution
    view = _view(ctx, item_id)
    assert view["kind"] == "page" and view["crops"] == [] and view["notice"] == NO_CROP
    assert view["originalPage"] == {"extractionId": SOL, "spanId": "m1", "outlineSpanIds": ["m1"],
                                    "sourceId": "src_sol"}


def test_a_block_whose_text_beside_the_stem_gives_the_answer_away_gives_no_crop(solved, warm):
    """No solution lead, but the words beside the statement state the
    expected answer (``tutor_qa.span_leaks_expected``) while the statement
    does not."""

    paths, ctx, repository = solved
    with repository.connection() as connection:
        connection.execute("UPDATE source_document_blocks SET text='Compute 7+5. The answer is 12.' WHERE span_id='m1'")
        connection.commit()
    (item_id,) = _import(paths, repository, [("m1", "Compute 7+5. The answer is 12.")], ["Compute 7+5."],
                         expected_answer_md="12")
    view = _view(ctx, item_id)
    assert view["crops"] == [] and view["notice"] == NO_CROP


# -- (A) unchanged: a multi-item split, and a statement over several blocks ---------------------------


def test_a_split_selection_still_crops_each_items_own_block(solved, warm):
    paths, ctx, repository = solved
    first, second = _import(paths, repository, [("p1", "Exercise 3. Compute 2+2."),
                                                ("m1", "Exercise 4. Compute 3+3. Solution: 3+3 = 6.")],
                            ["Compute 2+2.", "Compute 3+3."], expected_answer_md="4")
    assert _owned(paths, first) == [True, False] and _owned(paths, second) == [False, True]
    assert [crop["spanIds"] for crop in _view(ctx, first)["crops"]] == [["p1"]]
    assert _view(ctx, second)["notice"] == NO_CROP     # its block holds its solution


def test_a_selection_level_edit_of_the_whole_passage_keeps_the_crop_but_not_the_solution(solved, warm):
    """The capture editor's OCR fix: one item whose statement is the whole
    edited passage is printed from the whole selection, less its solution."""

    from learnloop.content.authoring import exercise_authoring as EX
    from learnloop.content.authoring.ai_contracts import ExerciseAuthoring
    from tests.test_exercise_authoring import FakeClient, _item, _write_facet_registry

    paths, ctx, repository = solved
    _write_facet_registry(paths.root.parent)
    raw = {"nodes": [{"spanId": "p1", "quote": "Exercise 3. Compute 2+2."},
                     {"spanId": "q1", "quote": "Solution. The sum is 4."}],
           "editedText": "Exercise 3. Compute 2 + 2.\n\nSolution. The sum is 4."}
    client = FakeClient(ExerciseAuthoring(items=[_item(statement_md="Exercise 3. Compute 2 + 2. Solution. The sum is 4.",
                                                       expected_answer_md="4")]))
    (summary,) = EX.import_exercises(paths.root, repository, client, extraction_id=SOL, raw_selection=raw,
                                     source_id="src_sol")["items"]
    assert _owned(paths, summary["practice_item_id"]) == [True, True]
    assert [crop["spanIds"] for crop in _view(ctx, summary["practice_item_id"])["crops"]] == [["p1"]]
    # Part of the edited passage only: ownership can't be read, the charged page only.
    client = FakeClient(ExerciseAuthoring(items=[_item(statement_md="Exercise 3. Compute 2 + 2.",
                                                       expected_answer_md="4")]))
    raw["editedText"] = "Exercise 3. Compute 2 + 2.\n\nSolution. The sum is four."
    (summary,) = EX.import_exercises(paths.root, repository, client, extraction_id=SOL, raw_selection=raw,
                                     source_id="src_sol")["items"]
    assert _owned(paths, summary["practice_item_id"]) == [False, False]
    assert _view(ctx, summary["practice_item_id"])["notice"] == NO_CROP


def test_a_canonical_exercise_never_crops_a_solution_block_it_names(solved, warm):
    """The same guard holds for the sources service's ``canonical_exercise``."""

    paths, ctx, _repository = solved
    path = next(paths.root.rglob(f"{ITEM}.yaml"))
    payload = read_yaml(path)
    payload["canonical_exercise"] = {"source_id": "src_sol", "revision_id": "rev_sol", "extraction_id": SOL,
                                     "span_ids": ["p1", "q1"], "label": "Exercise 3", "relation": "verbatim"}
    write_yaml(path, payload)
    view = _view(ctx, ITEM)
    assert [crop["spanIds"] for crop in view["crops"]] == [["p1"]]


# -- (C) CA1 polish: the book's learner title, and an empty exercise label ----------------------------


def test_a_book_without_a_display_title_is_named_by_its_learner_title(book, warm):
    paths, ctx, repository = book
    _seed(paths.root, repository, display_title=None)
    (item_id,) = _import(paths, repository, [("p1", "Exercise 3. Compute 2+2.")], ["Compute 2+2."],
                         expected_answer_md="4")
    view = _view(ctx, item_id)
    assert view["label"] == "as printed (Linear Algebra Done Right p.1)"
    assert view["locator"]["sourceTitle"] == "Linear Algebra Done Right"


def test_the_canonical_exercise_dto_names_the_book_by_its_learner_title(book):
    paths, ctx, repository = book
    _seed(paths.root, repository, display_title="")
    path = next(paths.root.rglob(f"{ITEM}.yaml"))
    payload = read_yaml(path)
    payload["canonical_exercise"] = {"source_id": "src_sol", "revision_id": "rev_sol", "extraction_id": SOL,
                                     "span_ids": ["p1"], "label": "", "relation": "verbatim"}
    write_yaml(path, payload)
    ctx.reload(maintenance=False)
    from learnloop_sidecar.handlers.serializers import _canonical_exercise_dto

    vault, _ = ctx.require_vault()
    dto = _canonical_exercise_dto(repository, vault.practice_items[ITEM])["canonical_exercise"]
    assert dto["source_title"] == "Linear Algebra Done Right"


@pytest.mark.parametrize("label", ["", "   ", None])
def test_an_empty_exercise_label_is_no_label(solved, warm, label):
    paths, ctx, _repository = solved
    path = next(paths.root.rglob(f"{ITEM}.yaml"))
    payload = read_yaml(path)
    payload["canonical_exercise"] = {"source_id": "src_sol", "revision_id": "rev_sol", "extraction_id": SOL,
                                     "span_ids": ["p1"], "label": label, "relation": "verbatim"}
    write_yaml(path, payload)
    view = _view(ctx, ITEM)
    assert view["locator"]["exerciseLabel"] is None
    assert view["label"] == "as printed (Strang p.1)"
