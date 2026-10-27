"""Reader CA1, the Codex re-review of the Astra batch fixes (F1, F3, F5, F6).

* F1 (High, reopened): words before the statement in its block are allowed
  only when they are affirmatively a label or heading ("Exercise 6.", "(a)",
  "Problem 3.2:"). "The answer is 4. Compute 2+2." gives no free crop, though
  the leak matcher ignores the lone digit.
* F3 (Medium, reopened): a solution block that holds part of the statement
  only up to moved spaces ("3+3" printed, "3 + 3" in the prompt), or holds it
  in its middle, never leaves the rest of the problem printed alone: a free
  crop must account for the whole statement, else the whole crop is withheld.
* F5 (High): a selected figure is the problem's (its crop, its stimulus for
  a check on your own) only when the import author calls it ``stimulus``
  (the Astra redesign; these tests first pinned a lexical rule over the
  statement's words, and were rewritten). A completed answer graph selected
  with "Sketch y=x^2." is neither cropped nor shown cold; an input diagram
  ("the line shown") still is. A legacy import (no role recorded) keeps
  main's figure rule less solutions: the residual is an owner question.
* F6 (High): a kept figure keeps the learner's selected sub-box when the
  text gives no free crop, and when the figure is stimulus without textual
  ownership, so an answer inset elsewhere in the image block stays out of a
  check on your own.

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
from learnloop.reader.as_printed import NO_CROP, _is_label
from learnloop.vault.yaml_io import read_yaml, write_yaml
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

EXT = "ext_ca1_rereview"
NOW_ISO = "2026-01-01T00:00:00Z"
#: (span, type, page, bbox, colour, text).
LAYOUT = (
    ("s1", "Text", 0, [72.0, 100.0, 540.0, 140.0], RED, "Sketch y=x^2."),
    ("g1", "Figure", 0, [72.0, 150.0, 300.0, 330.0], GREEN, "A parabola through the origin."),
    ("t2", "Text", 0, [72.0, 350.0, 540.0, 390.0], RED, "Find the slope of the line shown. The slope is 2."),
    ("g2", "Figure", 0, [72.0, 400.0, 300.0, 580.0], GREEN, "A line through the origin."),
    ("p1", "Text", 1, [72.0, 50.0, 540.0, 90.0], BLUE, "The answer is 4. Compute 2+2."),
    ("a1", "Text", 1, [72.0, 100.0, 540.0, 140.0], RED, "Exercise 6. (a) Compute 2+2."),
    ("b1", "Text", 1, [72.0, 150.0, 540.0, 190.0], BLUE, "(b) Compute 3+3. We get 6."),
    ("c1", "Text", 1, [72.0, 200.0, 540.0, 240.0], BLUE, "We get 4. (b) Compute 3+3. We get 6."),
)
#: The answer inset inside g2's image block (no block of its own), and the
#: learner's selected sub-box of g2 that leaves it out.
INSET = [200.0, 500.0, 300.0, 580.0]
G2_REGION = {"spanId": "g2", "page": 0, "bbox": [72.0, 400.0, 190.0, 490.0]}


def _seed(root, repository) -> None:
    pages = []
    for page in (0, 1):
        image = Image.new("RGB", (612, 792), "white")
        draw = ImageDraw.Draw(image)
        for _span, _kind, block_page, bbox, colour, _text in LAYOUT:
            if block_page == page:
                draw.rectangle(bbox, fill=colour)
        if page == 0:
            draw.rectangle(INSET, fill=BLUE)
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
            ("src_rr", "pdf", "file:///nowhere/book.pdf", "Strang", "rev_rr", 1, NOW_ISO, NOW_ISO))
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            ("rev_rr", "src_rr", digest, None, NOW_ISO))
        connection.commit()
    blocks = [DocumentBlock.build(span_id=span, block_type=kind, text=text, ordinal=index, page=page, bbox=bbox,
                                  section_path=["6.1"])
              for index, (span, kind, page, bbox, _colour, text) in enumerate(LAYOUT, start=1)]
    unit = DocumentUnit(unit_id="u_rr", label="6.1", ordinal=0, semantic_hash="sha256:u_rr", page_start=0,
                        page_end=1, span_ids=[block.span_id for block in blocks])
    ir = DocumentIR(extractor="marker", extractor_version="1", units=[unit], blocks=blocks, assets=[],
                    health=ExtractionHealth())
    _persist(repository, ir, revision_id="rev_rr", extraction_id=EXT)


@pytest.fixture
def seeded(book):
    paths, ctx, repository = book
    _seed(paths.root, repository)
    return paths, ctx, repository


def _text(span: str) -> str:
    return next(text for name, _kind, _page, _bbox, _colour, text in LAYOUT if name == span)


def _import(paths, repository, spans: list[str], statement: str, answer: str, *, region=None,
            roles: dict[str, str] | None = None) -> str:
    from learnloop.content.authoring import exercise_authoring as EX
    from learnloop.content.authoring.ai_contracts import ExerciseAuthoring, FigureRolePayload
    from tests.test_exercise_authoring import FakeClient, _item, _write_facet_registry

    _write_facet_registry(paths.root.parent)
    raw = {"nodes": [{"spanId": span, "quote": _text(span)} for span in spans]}
    if region is not None:
        raw["region"] = region
    claims = [FigureRolePayload(span_id=span, role=role) for span, role in (roles or {}).items()]
    client = FakeClient(ExerciseAuthoring(items=[_item(statement_md=statement, expected_answer_md=answer,
                                                       figure_roles=claims)]))
    (summary,) = EX.import_exercises(paths.root, repository, client, extraction_id=EXT, raw_selection=raw,
                                     source_id="src_rr")["items"]
    return summary["practice_item_id"]


def _refs(paths, item_id: str) -> list[dict]:
    return read_yaml(next(paths.root.rglob(f"{item_id}.yaml")))["provenance"]["source_refs"]


def _set_prompt(paths, item_id: str, prompt: str) -> None:
    path = next(paths.root.rglob(f"{item_id}.yaml"))
    payload = read_yaml(path)
    payload["prompt"] = prompt
    write_yaml(path, payload)


def _record_solution(paths, repository, item_id: str, spans: list[str], solution: list[str]) -> None:
    from learnloop.content.authoring import source_exercise_import as SEI
    from learnloop.db.stores.source_service import update_import

    (row,) = SEI.record_reader_import(paths.root, repository, {"items": [{"practice_item_id": item_id}]},
                                      extraction_id=EXT, span_ids=spans, source_id="src_rr", revision_id="rev_rr")
    with repository.connection() as connection:
        update_import(connection, row["import_id"], updated_at=NOW_ISO,
                      verification={"book_solution": {"span_ids": solution, "page": 1}})
        connection.commit()


def _view(ctx, item_id: str) -> dict:
    ctx.reload(maintenance=False)
    return _call(ctx, "practice.as_printed", {"practiceItemId": item_id, "render": True})


def _no_free_crop(view: dict, span: str) -> None:
    assert view["kind"] == "page" and view["crops"] == [] and view["notice"] == NO_CROP
    assert view["originalPage"]["extractionId"] == EXT and view["originalPage"]["spanId"] == span


# -- F1: words before the statement must be a label --------------------------------------------------


def test_an_answer_before_the_statement_in_its_block_gives_no_free_crop(seeded, warm):
    from learnloop.tutor.tutor_qa import span_leaks_expected

    paths, ctx, repository = seeded
    assert not span_leaks_expected("The answer is 4.", "4")       # the leak matcher alone calls it safe
    item_id = _import(paths, repository, ["p1"], "Compute 2+2.", "4")
    assert _owned(paths, item_id) == [True]
    _no_free_crop(_view(ctx, item_id), "p1")


@pytest.mark.parametrize("prefix", ["Exercise 6.", "(a)", "Exercise 6. (a)", "Problem 3.2:", "12.", "(iv)",
                                    "Exercises", "Q3.", "*5.", "Exercise 1.2.3 (b)", "§2 Problem 4"])
def test_labels_and_headings_are_labels(prefix):
    assert _is_label(prefix)


@pytest.mark.parametrize("prefix", ["The answer is 4.", "Hint: factor.", "Answer: 4", "We get 6.", "No.", "Q.",
                                    "Solution.", "Note that x = 2.", "Exercise 6. The answer is 4.", "x", "mix"])
def test_other_words_before_the_statement_are_not_labels(prefix):
    assert not _is_label(prefix)


# -- F3: a partial print up to moved spaces or a solution holding the statement in its middle -------------


def test_a_solution_block_holding_part_of_the_statement_up_to_spaces_withholds_the_crop(seeded, warm):
    paths, ctx, repository = seeded
    item_id = _import(paths, repository, ["a1", "b1"], "(a) Compute 2+2. (b) Compute 3+3.", "4 and 6")
    assert _owned(paths, item_id) == [True, True]
    # The learner moved spaces in part (b) (the review's scenario).
    _set_prompt(paths, item_id, "(a) Compute 2+2. (b) Compute 3 + 3.")
    _record_solution(paths, repository, item_id, ["a1", "b1"], ["b1"])
    _no_free_crop(_view(ctx, item_id), "a1")


def test_a_solution_block_holding_the_statement_in_its_middle_withholds_the_crop(seeded, warm):
    paths, ctx, repository = seeded
    item_id = _import(paths, repository, ["a1", "c1"], "(a) Compute 2+2.", "4 and 6")
    _mark_every_block_owned(paths, item_id)
    _set_prompt(paths, item_id, "(a) Compute 2+2. (b) Compute 3+3.")
    _record_solution(paths, repository, item_id, ["a1", "c1"], ["c1"])
    _no_free_crop(_view(ctx, item_id), "a1")


def test_a_statement_the_kept_blocks_print_whole_still_crops(seeded, warm):
    """The affirmative case: (a) alone, its own block printing all of it."""

    paths, ctx, repository = seeded
    item_id = _import(paths, repository, ["a1", "b1"], "(a) Compute 2+2.", "4")
    _record_solution(paths, repository, item_id, ["a1", "b1"], ["b1"])
    assert [crop["spanIds"] for crop in _view(ctx, item_id)["crops"]] == [["a1"]]


# -- F5: an input diagram, not a completed answer diagram ---------------------------------------------------


def test_a_completed_answer_graph_selected_with_sketch_is_not_the_problems(seeded, warm):
    paths, ctx, repository = seeded
    item_id = _import(paths, repository, ["s1", "g1"], "Sketch y=x^2.", "a parabola")
    assert _owned(paths, item_id) == [True, False]
    assert [ref.get("figure_role") for ref in _refs(paths, item_id)] == [None, "unrelated"]
    view = _view(ctx, item_id)
    assert [crop["spanIds"] for crop in view["crops"]] == [["s1"]]
    assert _share(_image(view["crops"][0]["image"]), GREEN) == 0


def test_a_completed_answer_graph_is_not_shown_in_a_check_on_your_own(seeded, cold):
    paths, ctx, repository = seeded
    item_id = _import(paths, repository, ["s1", "g1"], "Sketch y=x^2.", "a parabola")
    assert _view(ctx, item_id)["kind"] == "none"


def _as_legacy(paths, item_id: str) -> None:
    """An import before the redesign: every block owned, no figure role."""

    _mark_every_block_owned(paths, item_id)
    path = next(paths.root.rglob(f"{item_id}.yaml"))
    payload = read_yaml(path)
    for ref in payload["provenance"]["source_refs"]:
        ref.pop("figure_role", None)
    write_yaml(path, payload)


@pytest.mark.parametrize("cold_check", [False, True])
def test_the_legacy_residual_an_old_mark_on_an_unmarked_answer_graph_keeps_mains_rule(seeded, monkeypatch,
                                                                                         cold_check):
    """The documented residual (rewritten: the lexical rule hid this graph by
    its statement's words). An import before the redesign recorded no role;
    nothing marks the completed graph as an answer (no solution span, role
    or lead), so main's figure rule holds: an owned figure before any
    solution prints, and a check on your own shows it. Owner question in
    ``docs/reviews/astra-batch1-fixes.md`` (Redesign)."""

    import learnloop.intent.checks as checks

    monkeypatch.setattr(checks, "served_check",
                        lambda *args, **kwargs: {"cold": True, "locators_hidden": True} if cold_check else None)
    paths, ctx, repository = seeded
    item_id = _import(paths, repository, ["s1", "g1"], "Sketch y=x^2.", "a parabola")
    _as_legacy(paths, item_id)
    view = _view(ctx, item_id)
    assert view["kind"] == ("figure" if cold_check else "page")
    assert _share(_image(view["crops"][-1]["image"]), GREEN) > 0.9


def test_a_required_input_diagram_stays_the_problems_stimulus(seeded, cold):
    paths, ctx, repository = seeded
    item_id = _import(paths, repository, ["t2", "g2"], "Find the slope of the line shown.", "2",
                      roles={"g2": "stimulus"})
    assert [ref.get("figure_role") for ref in _refs(paths, item_id)] == [None, "stimulus"]
    view = _view(ctx, item_id)
    assert view["kind"] == "figure" and len(view["crops"]) == 1
    assert _share(_image(view["crops"][0]["image"]), GREEN) > 0.5


# -- F6: a kept figure keeps its selected sub-box ----------------------------------------------------------


def test_a_kept_figure_keeps_its_sub_box_when_the_text_gives_no_free_crop(seeded, cold):
    paths, ctx, repository = seeded
    item_id = _import(paths, repository, ["t2", "g2"], "Find the slope of the line shown.", "2", region=G2_REGION,
                      roles={"g2": "stimulus"})
    view = _view(ctx, item_id)
    assert view["kind"] == "figure" and len(view["crops"]) == 1
    image = _image(view["crops"][0]["image"])
    assert _share(image, GREEN) > 0.9 and _share(image, BLUE) == 0      # the answer inset stays out


def test_the_sub_box_is_kept_while_warm_too(seeded, warm):
    paths, ctx, repository = seeded
    item_id = _import(paths, repository, ["t2", "g2"], "Find the slope of the line shown.", "2", region=G2_REGION)
    _no_free_crop(_view(ctx, item_id), "t2")                             # words after the statement


def test_a_stimulus_figure_without_textual_ownership_keeps_its_sub_box(seeded, cold):
    paths, ctx, repository = seeded
    # A paraphrase: the full selection is the prompt, nothing is owned, the figure is stimulus.
    item_id = _import(paths, repository, ["t2", "g2"], "What is the slope of that line?", "2", region=G2_REGION,
                      roles={"g2": "stimulus"})
    assert _owned(paths, item_id) == [False, True]                      # no text owned; the figure by its role
    view = _view(ctx, item_id)
    assert view["kind"] == "figure" and len(view["crops"]) == 1
    image = _image(view["crops"][0]["image"])
    assert _share(image, GREEN) > 0.9 and _share(image, BLUE) == 0


# -- the rules themselves --------------------------------------------------------------------------------


def test_a_placement_starts_and_ends_where_words_do():
    from learnloop.reader.as_printed import _placement

    assert _placement("4", "Compute 2+24.") is None                     # never inside a word
    placed = _placement("(b) Compute 3+3. We get 6.", "(a) Compute 2+2. (b) Compute 3 + 3.")
    assert placed is not None and placed.after == "We get 6." and placed.before == ""
    placed = _placement("Exercise 6. (a) Compute 2+2.", "(a) Compute 2 + 2.")
    assert placed is not None and placed.before == "Exercise 6." and placed.after == ""
