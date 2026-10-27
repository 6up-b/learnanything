"""Reader CA1, the Astra redesign: the free crop shows only the problem, by
rules that are conservative by construction (owner 2026-10-26: "i would hope
that crop excludes the solution").

The closed checklist of the reopened final verify (Codex job
20261027-042324-138aCi):

* F2 (High): a required input graph ("Estimate f(2) from the graph.") is the
  problem's stimulus because the import author said so in its structured
  output, so a check on your own shows it. No words of the statement decide.
* F3 (Medium): statement coverage comes only from blocks that print; a
  dropped solution block holding part (b) never leaves part (a) printed alone.
* F5 (High): an output diagram is not stimulus ("Draw the diagram ..." with
  the completed diagram), and a figure whose number contradicts the
  statement's ("Use Figure 1" with only Figure 2 selected) is refused even
  when the author calls it stimulus.
* F6 (High): crops are never merged, so an excluded sub-box of a kept figure
  (an answer inset) never comes back through a union rectangle.

And the legacy rule (imports with no recorded figure role), the canonical
exercise's recorded roles, and the author's figure context.

A real PDF is drawn here (no book text is committed); every model is a fake.
"""

from __future__ import annotations

import hashlib
import io

import pytest
from PIL import Image, ImageDraw

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.content.authoring.ai_contracts import FigureRolePayload
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.ingest.originals import store_original_bytes
from learnloop.reader.as_printed import FIGURE_LABEL, NO_CROP
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.test_reader_ca1_as_printed import (  # noqa: F401 - fixtures
    BLUE,
    GREEN,
    GREY,
    RED,
    _call,
    _image,
    _share,
    book,
    cold,
    warm,
)
from tests.test_source_inventory import _persist

EXT = "ext_ca1_redesign"
NOW_ISO = "2026-01-01T00:00:00Z"
#: (span, type, page, bbox, colour, text). Red: a problem's text; green: an
#: input figure; blue: an answer, a solution, or an answer figure.
LAYOUT = (
    # F2: a required input graph the statement names only as "the graph".
    ("q1", "Text", 0, [72.0, 100.0, 540.0, 140.0], RED, "Estimate f(2) from the graph."),
    ("g1", "Figure", 0, [72.0, 150.0, 300.0, 330.0], GREEN, "Axes and a curve."),
    # F5 (1): an output instruction with the completed, unlabelled answer diagram.
    ("d1", "Text", 0, [72.0, 350.0, 540.0, 390.0], RED,
     "Draw the diagram of the circuit with its equivalent resistance marked."),
    ("d2", "Figure", 0, [72.0, 400.0, 300.0, 580.0], BLUE, "A circuit with R = 6 ohm marked."),
    # F5 (2): the statement names Figure 1; only Figure 2 (completed) is selected.
    ("u1", "Text", 1, [72.0, 50.0, 540.0, 90.0], RED, "Use Figure 1 to sketch the transformed graph."),
    ("u2", "Figure", 1, [72.0, 100.0, 300.0, 280.0], BLUE, "Figure 2. Completed transformed graph."),
    # F3: part (b) sits in a block the import's check names as solution.
    ("a1", "Text", 1, [72.0, 300.0, 540.0, 330.0], RED, "(a) Compute 2+2."),
    ("b1", "Text", 1, [72.0, 340.0, 540.0, 370.0], BLUE, "(b) Compute 3+3."),
    ("s1", "Text", 1, [72.0, 380.0, 540.0, 410.0], BLUE, "We get 6."),
    # F6: two figures the statement uses; Figure 1 holds an answer inset
    # (no block of its own) outside the learner's selected sub-box.
    ("t6", "Text", 2, [0.0, 50.0, 540.0, 90.0], RED, "Compare Figure 1 with Figure 2."),
    ("h1", "Figure", 2, [0.0, 110.0, 100.0, 210.0], GREEN, "Figure 1. A line."),
    ("h2", "Figure", 2, [0.0, 220.0, 100.0, 320.0], GREEN, "Figure 2. A parabola."),
    # Legacy: a problem, its solution, and a figure before and after the solution.
    ("p7", "Text", 3, [72.0, 50.0, 540.0, 90.0], RED, "Exercise 7. Find the shaded area."),
    ("k6", "Figure", 3, [72.0, 100.0, 300.0, 280.0], GREEN, "The shaded region."),
    ("r7", "Text", 3, [72.0, 300.0, 540.0, 340.0], BLUE, "Solution. The area is 2."),
    ("k7", "Figure", 3, [72.0, 350.0, 300.0, 530.0], BLUE, "The region, split in two."),
    # Sol verify 2: a required graph whose title starts with the word "Solution".
    ("c9", "Text", 4, [72.0, 50.0, 540.0, 90.0], RED, "Estimate the concentration at t = 5 s from the graph."),
    ("g9", "Figure", 4, [72.0, 100.0, 300.0, 280.0], GREEN, "Solution concentration (mol/L) versus time (s)."),
    # Sol verify 3: overlapping boxes. Figure 3's sub-box leaves out an
    # inset that Figure 4's box overlaps; a problem's box overlaps its
    # dropped solution block.
    ("t8", "Text", 5, [0.0, 20.0, 300.0, 60.0], RED, "Compare Figure 3 with Figure 4."),
    ("fa", "Figure", 5, [0.0, 100.0, 100.0, 200.0], GREEN, "Figure 3. A line."),
    ("fb", "Figure", 5, [80.0, 100.0, 180.0, 200.0], GREEN, "Figure 4. A parabola."),
    ("p8", "Text", 5, [72.0, 300.0, 540.0, 350.0], RED, "Exercise 8. Compute 5+5."),
    ("r8", "Text", 5, [72.0, 340.0, 540.0, 380.0], BLUE, "Solution. The sum is 10."),
    # Sol verify ruling: Figure A's unselected rest covers a retained Figure B.
    ("ta", "Text", 6, [0.0, 20.0, 300.0, 60.0], RED, "Compare Figure 5 with Figure 6."),
    ("fA", "Figure", 6, [0.0, 90.0, 240.0, 230.0], GREEN, "Figure 5. A line."),
    ("fB", "Figure", 6, [120.0, 100.0, 220.0, 200.0], GREEN, "Figure 6. A parabola."),
    # A scale label extracted as its own block over a retained graph.
    ("s7", "Text", 7, [72.0, 20.0, 540.0, 60.0], RED, "Read y at x = 2 from the plot."),
    ("gp", "Figure", 7, [72.0, 80.0, 300.0, 260.0], GREEN, "The plot of y against x."),
    ("lb", "Text", 7, [100.0, 240.0, 200.0, 255.0], GREY, "0 1 2 3"),
    # Sol verify of 788241756: a sibling's answer figure overlapping a retained figure.
    ("tq", "Text", 13, [20.0, 20.0, 540.0, 60.0], RED, "Find the slope of the line in Figure 7."),
    ("tz", "Text", 13, [20.0, 300.0, 540.0, 340.0], RED, "Sketch the completed graph."),
    ("fs", "Figure", 13, [20.0, 100.0, 200.0, 250.0], GREEN, "Figure 7. A line."),
    ("fx", "Figure", 13, [150.0, 150.0, 230.0, 230.0], BLUE, "Figure 8. The completed sketch."),
) + tuple(
    # Sol verify ruling: a problem's box inside an excluded box, once per
    # exclusion reason (pages 8-12): (P) the problem, (E) the enclosing box.
    entry for page, (number, kind, text) in enumerate([
        ("6", "Text", "The sum is twelve."),                     # a book-solution span
        ("7", "Text", "The sum is fourteen."),                   # a solution role
        ("8", "Text", "Solution. The sum is 16."),               # a heading-led solution
        ("9", "Figure", "A completed graph."),                   # a figure refused as an answer
        ("4", "Figure", "The worked construction."),             # a figure refused as worked
    ], start=8)
    for entry in ((f"E{page}", kind, page, [10.0, 30.0, 260.0, 200.0], BLUE, text),
                  (f"P{page}", "Text", page, [40.0, 60.0, 220.0, 130.0], RED,
                   f"Exercise {page}. Compute {number}+{number}."))
)
#: F6: the answer inset inside h1's block, and the learner's sub-box of h1
#: leaving it out; Sol verify 3: the inset inside Figure 3 (fa) that its
#: sub-box leaves out and Figure 4's box (fb) overlaps.
INSETS = ((2, [80.0, 180.0, 100.0, 210.0]), (5, [85.0, 105.0, 95.0, 120.0]),
          *((page, [200.0, 110.0, 215.0, 125.0]) for page in range(8, 13)))   # E's ink inside P's box
H1_REGION = {"spanId": "h1", "page": 2, "bbox": [10.0, 120.0, 40.0, 150.0]}
FA_REGION = {"spanId": "fa", "page": 5, "bbox": [0.0, 100.0, 80.0, 200.0]}
A_REGION = {"spanId": "fA", "page": 6, "bbox": [0.0, 100.0, 100.0, 200.0]}
PAGES = 14


def _seed(root, repository) -> None:
    pages = []
    for page in range(PAGES):
        image = Image.new("RGB", (612, 792), "white")
        draw = ImageDraw.Draw(image)
        for _span, _kind, block_page, bbox, colour, _text in LAYOUT:
            if block_page == page:
                draw.rectangle(bbox, fill=colour)
        for inset_page, inset in INSETS:
            if page == inset_page:
                draw.rectangle(inset, fill=BLUE)
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
            ("src_rd", "pdf", "file:///nowhere/book.pdf", "Strang", "rev_rd", 1, NOW_ISO, NOW_ISO))
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            ("rev_rd", "src_rd", digest, None, NOW_ISO))
        connection.commit()
    blocks = [DocumentBlock.build(span_id=span, block_type=kind, text=text, ordinal=index, page=page, bbox=bbox,
                                  section_path=["6.1"])
              for index, (span, kind, page, bbox, _colour, text) in enumerate(LAYOUT, start=1)]
    unit = DocumentUnit(unit_id="u_rd", label="6.1", ordinal=0, semantic_hash="sha256:u_rd", page_start=0,
                        page_end=PAGES - 1, span_ids=[block.span_id for block in blocks])
    ir = DocumentIR(extractor="marker", extractor_version="1", units=[unit], blocks=blocks, assets=[],
                    health=ExtractionHealth())
    _persist(repository, ir, revision_id="rev_rd", extraction_id=EXT)


@pytest.fixture
def seeded(book):
    paths, ctx, repository = book
    _seed(paths.root, repository)
    return paths, ctx, repository


def _text(span: str) -> str:
    return next(text for name, _kind, _page, _bbox, _colour, text in LAYOUT if name == span)


def _import(paths, repository, spans: list[str], statement: str, answer: str, *,
            roles: dict[str, str] | None = None, region=None) -> tuple[str, list]:
    """One single-exercise Reader import; ``roles``: the author's figure roles."""

    from learnloop.content.authoring import exercise_authoring as EX
    from learnloop.content.authoring.ai_contracts import ExerciseAuthoring
    from tests.test_exercise_authoring import FakeClient, _item, _write_facet_registry

    _write_facet_registry(paths.root.parent)
    raw = {"nodes": [{"spanId": span, "quote": _text(span)} for span in spans]}
    if region is not None:
        raw["region"] = region
    claims = [FigureRolePayload(span_id=span, role=role) for span, role in (roles or {}).items()]
    client = FakeClient(ExerciseAuthoring(items=[_item(statement_md=statement, expected_answer_md=answer,
                                                       figure_roles=claims)]))
    (summary,) = EX.import_exercises(paths.root, repository, client, extraction_id=EXT, raw_selection=raw,
                                     source_id="src_rd")["items"]
    return summary["practice_item_id"], client.calls


def _refs(paths, item_id: str) -> dict[str, dict]:
    refs = read_yaml(next(paths.root.rglob(f"{item_id}.yaml")))["provenance"]["source_refs"]
    return {ref["locator"].rsplit("/", 1)[1]: ref for ref in refs}


def _view(ctx, item_id: str) -> dict:
    ctx.reload(maintenance=False)
    return _call(ctx, "practice.as_printed", {"practiceItemId": item_id, "render": True})


def _crop_spans(view: dict) -> list[list[str]]:
    return [crop["spanIds"] for crop in view["crops"]]


def _no_free_crop(view: dict, span: str) -> None:
    assert view["kind"] == "page" and view["crops"] == [] and view["notice"] == NO_CROP
    assert view["originalPage"]["extractionId"] == EXT and view["originalPage"]["spanId"] == span


def _record_solution(paths, repository, item_id: str, spans: list[str], solution: list[str]) -> None:
    from learnloop.content.authoring import source_exercise_import as SEI
    from learnloop.db.stores.source_service import update_import

    (row,) = SEI.record_reader_import(paths.root, repository, {"items": [{"practice_item_id": item_id}]},
                                      extraction_id=EXT, span_ids=spans, source_id="src_rd", revision_id="rev_rd")
    with repository.connection() as connection:
        update_import(connection, row["import_id"], updated_at=NOW_ISO,
                      verification={"book_solution": {"span_ids": solution, "page": 1}})
        connection.commit()


def _as_legacy(paths, item_id: str) -> None:
    """An import written before the redesign: every block owned (the old
    single-exercise rule), no figure role recorded."""

    path = next(paths.root.rglob(f"{item_id}.yaml"))
    payload = read_yaml(path)
    for ref in payload["provenance"]["source_refs"]:
        ref["owned"] = True
        ref.pop("figure_role", None)
        ref.pop("figure_role_rejected", None)
    write_yaml(path, payload)


# -- F2: a required input graph is the problem's stimulus ------------------------------------------------


def test_f2_a_required_input_graph_is_shown_in_a_check_on_your_own(seeded, cold):
    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["q1", "g1"], "Estimate f(2) from the graph.", "about 3",
                              roles={"g1": "stimulus"})
    view = _view(ctx, item_id)
    assert view["kind"] == "figure" and view["label"] == FIGURE_LABEL and len(view["crops"]) == 1
    assert _share(_image(view["crops"][0]["image"]), GREEN) > 0.9
    assert _refs(paths, item_id)["g1"]["figure_role"] == "stimulus" and _refs(paths, item_id)["g1"]["owned"] is True


def test_f2_the_input_graph_prints_with_the_problem_outside_a_check(seeded, warm):
    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["q1", "g1"], "Estimate f(2) from the graph.", "about 3",
                              roles={"g1": "stimulus"})
    assert _crop_spans(_view(ctx, item_id)) == [["q1"], ["g1"]]


# -- F3: coverage only from blocks that print -------------------------------------------------------------


def test_f3_a_partial_problem_gives_no_free_crop(seeded, warm):
    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["a1", "b1", "s1"], "(a) Compute 2+2. (b) Compute 3+3.", "4 and 6")
    _record_solution(paths, repository, item_id, ["a1", "b1", "s1"], ["b1", "s1"])
    # Part (b) is wholly inside the statement but in a dropped block: it prints nothing.
    _no_free_crop(_view(ctx, item_id), "a1")


def test_f3_up_to_moved_spaces_too(seeded, warm):
    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["a1", "b1", "s1"], "(a) Compute 2+2. (b) Compute 3+3.", "4 and 6")
    path = next(paths.root.rglob(f"{item_id}.yaml"))
    payload = read_yaml(path)
    payload["prompt"] = "(a) Compute 2+2. (b) Compute 3 + 3."
    write_yaml(path, payload)
    _record_solution(paths, repository, item_id, ["a1", "b1", "s1"], ["b1", "s1"])
    _no_free_crop(_view(ctx, item_id), "a1")


def test_f3_the_whole_problem_in_printed_blocks_still_crops(seeded, warm):
    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["a1", "b1", "s1"], "(a) Compute 2+2. (b) Compute 3+3.", "4 and 6")
    _record_solution(paths, repository, item_id, ["a1", "b1", "s1"], ["s1"])
    view = _view(ctx, item_id)
    assert _crop_spans(view) == [["a1"], ["b1"]]                        # never the solution block s1
    assert view["originalPage"]["outlineSpanIds"] == ["a1", "b1"]


# -- F5: an output diagram, or a contradicting figure number, is never stimulus ---------------------------


@pytest.mark.parametrize("roles", [{"d2": "answer"}, {}], ids=["author_says_answer", "author_says_nothing"])
def test_f5_a_completed_answer_diagram_is_not_stimulus(seeded, cold, roles):
    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["d1", "d2"],
                              "Draw the diagram of the circuit with its equivalent resistance marked.", "R = 6 ohm",
                              roles=roles)
    ref = _refs(paths, item_id)["d2"]
    assert ref["owned"] is False and ref["figure_role"] == (roles.get("d2") or "unrelated")
    assert _view(ctx, item_id)["kind"] == "none"


def test_f5_a_completed_answer_diagram_never_prints_for_free(seeded, warm):
    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["d1", "d2"],
                              "Draw the diagram of the circuit with its equivalent resistance marked.", "R = 6 ohm",
                              roles={"d2": "answer"})
    view = _view(ctx, item_id)
    assert _crop_spans(view) == [["d1"]] and _share(_image(view["crops"][0]["image"]), BLUE) == 0


@pytest.mark.parametrize("roles", [{"u2": "stimulus"}, {}], ids=["author_says_stimulus", "author_says_nothing"])
def test_f5_a_figure_whose_number_contradicts_the_statement_is_refused(seeded, cold, roles):
    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["u1", "u2"], "Use Figure 1 to sketch the transformed graph.",
                              "a shifted parabola", roles=roles)
    ref = _refs(paths, item_id)["u2"]
    assert ref["owned"] is False
    if roles:
        assert ref["figure_role"] == "stimulus" and ref["figure_role_rejected"] == "figure_number_mismatch"
    assert _view(ctx, item_id)["kind"] == "none"


# -- F6: never a merged rectangle --------------------------------------------------------------------------


def _blue_free(view: dict) -> None:
    for crop in view["crops"]:
        assert _share(_image(crop["image"]), BLUE) == 0, crop


def test_f6_an_excluded_inset_never_returns_through_a_merged_crop(seeded, warm):
    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["t6", "h1", "h2"], "Compare Figure 1 with Figure 2.", "one is curved",
                              roles={"h1": "stimulus", "h2": "stimulus"}, region=H1_REGION)
    view = _view(ctx, item_id)
    _blue_free(view)                                                     # no pixel of the inset
    assert _crop_spans(view) == [["t6"], ["h1"], ["h2"]]
    assert view["crops"][1]["bbox"] == [10.0, 120.0, 40.0, 150.0]       # the sub-box, alone
    assert view["crops"][2]["bbox"] == [0.0, 220.0, 100.0, 320.0]


def test_f6_and_in_a_check_on_your_own(seeded, cold):
    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["t6", "h1", "h2"], "Compare Figure 1 with Figure 2.", "one is curved",
                              roles={"h1": "stimulus", "h2": "stimulus"}, region=H1_REGION)
    view = _view(ctx, item_id)
    _blue_free(view)
    assert view["kind"] == "figure" and len(view["crops"]) == 2


def test_f6_and_when_the_text_gives_no_free_crop(seeded, cold):
    paths, ctx, repository = seeded
    # A paraphrase: no text is owned, the figures are still the author's stimulus.
    item_id, _calls = _import(paths, repository, ["t6", "h1", "h2"], "How do the two figures differ?",
                              "one is curved", roles={"h1": "stimulus", "h2": "stimulus"}, region=H1_REGION)
    view = _view(ctx, item_id)
    _blue_free(view)
    assert view["kind"] == "figure" and len(view["crops"]) == 2


def test_f6_crop_boxes_returns_one_crop_per_retained_region():
    from learnloop.reader.as_printed import crop_boxes

    own = [DocumentBlock.build(span_id=span, block_type=kind, text=span, ordinal=index, page=page, bbox=bbox)
           for index, (span, kind, page, bbox, _c, _t) in enumerate(LAYOUT, start=1) if span in ("h1", "h2")]
    crops, skipped = crop_boxes(own, {"h1": (2, (10.0, 120.0, 40.0, 150.0))})
    assert [(crop.span_ids, crop.bbox) for crop in crops] == [
        (("h1",), (10.0, 120.0, 40.0, 150.0)), (("h2",), (0.0, 220.0, 100.0, 320.0))]
    assert skipped == []


# -- legacy imports: no figure role recorded ------------------------------------------------------------


def test_legacy_a_figure_after_the_solution_is_left_to_the_original_page(seeded, warm):
    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["p7", "k6", "r7", "k7"], "Find the shaded area.", "2")
    _as_legacy(paths, item_id)
    view = _view(ctx, item_id)
    # The text and the figure before the solution print; the solution never;
    # the figure after it only on the original page (one hint before Submit).
    assert _crop_spans(view) == [["p7"], ["k6"]]
    _blue_free(view)
    assert view["originalPage"]["spanId"] == "p7"


def test_legacy_a_check_on_your_own_keeps_mains_figures_less_solutions(seeded, cold):
    """The page cannot open during a check on your own, so an owned figure
    shows unless it is a solution block (main's rule less solutions): the
    problem stays answerable. The residual is an owner question."""

    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["p7", "k6", "r7", "k7"], "Find the shaded area.", "2")
    _as_legacy(paths, item_id)
    view = _view(ctx, item_id)
    assert view["kind"] == "figure" and len(view["crops"]) == 2
    _record_solution(paths, repository, item_id, ["p7", "k6", "r7", "k7"], ["r7", "k7"])
    view = _view(ctx, item_id)
    assert view["kind"] == "figure" and len(view["crops"]) == 1
    assert _share(_image(view["crops"][0]["image"]), GREEN) > 0.9


def test_legacy_a_figure_on_the_solution_spans_never_prints(seeded, warm):
    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["p7", "k6", "r7", "k7"], "Find the shaded area.", "2")
    _as_legacy(paths, item_id)
    _record_solution(paths, repository, item_id, ["p7", "k6", "r7", "k7"], ["k6"])
    view = _view(ctx, item_id)
    assert _crop_spans(view) == [["p7"]]
    assert view["originalPage"]["outlineSpanIds"] == ["p7"]


# -- the canonical exercise: a recorded role is honoured ------------------------------------------------


def test_a_canonical_exercise_never_shows_a_figure_its_import_refused(seeded, cold):
    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["d1", "d2"],
                              "Draw the diagram of the circuit with its equivalent resistance marked.", "R = 6 ohm",
                              roles={"d2": "answer"})
    path = next(paths.root.rglob(f"{item_id}.yaml"))
    payload = read_yaml(path)
    payload["canonical_exercise"] = {"source_id": "src_rd", "revision_id": "rev_rd", "extraction_id": EXT,
                                     "span_ids": ["d1", "d2"], "label": "Exercise 9", "relation": "verbatim"}
    write_yaml(path, payload)
    assert _view(ctx, item_id)["kind"] == "none"


# -- the author: figures in its context, roles validated ---------------------------------------------------


def test_the_author_sees_the_selections_figures_and_their_instructions(seeded):
    from learnloop.content.authoring.ai_contracts import FIGURE_ROLE_INSTRUCTIONS, exercise_authoring_prompt

    paths, _ctx, repository = seeded
    _item_id, calls = _import(paths, repository, ["q1", "g1"], "Estimate f(2) from the graph.", "about 3",
                              roles={"g1": "stimulus"})
    (context,) = calls
    assert context.figures == {"blocks": [{"span_id": "g1", "text": "Axes and a curve."}],
                               "instructions": FIGURE_ROLE_INSTRUCTIONS}
    assert FIGURE_ROLE_INSTRUCTIONS in exercise_authoring_prompt(context)


def test_a_selection_without_a_figure_sends_no_figure_context(seeded):
    from learnloop.content.authoring.ai_contracts import exercise_authoring_prompt

    paths, _ctx, repository = seeded
    _item_id, calls = _import(paths, repository, ["a1"], "(a) Compute 2+2.", "4")
    (context,) = calls
    assert context.figures == {}
    assert '"figures"' not in exercise_authoring_prompt(context)


def test_figure_roles_are_validated_never_widened():
    from learnloop.content.authoring.exercise_authoring import _figure_roles

    figures = {"f1": "Figure 1. Axes.", "f2": "Figure 2. The completed graph.", "g": "A curve."}
    roles = _figure_roles({"f1": "stimulus", "f2": "stimulus", "g": "stimulus", "zz": "stimulus"}, figures,
                          "Use Figure 1.", claimed_elsewhere=set())
    assert roles == {"f1": ("stimulus", None), "f2": ("stimulus", "figure_number_mismatch"),
                     "g": ("stimulus", None)}        # an unnumbered figure is not contradicted; "zz" is not selected
    # A figure the author did not name is unrelated; one another item calls its answer is refused.
    roles = _figure_roles({"f1": "stimulus"}, figures, "Compare them.", claimed_elsewhere={"f1"})
    assert roles == {"f1": ("stimulus", "another_exercise_answer"), "f2": ("unrelated", None),
                     "g": ("unrelated", None)}


def test_two_claims_for_one_figure_resolve_away_from_stimulus():
    from learnloop.content.authoring.exercise_authoring import _claimed_roles
    from tests.test_exercise_authoring import _item

    for claims in (["stimulus", "answer"], ["answer", "stimulus"]):
        entry = _item(figure_roles=[FigureRolePayload(span_id="f", role=role) for role in claims])
        assert _claimed_roles(entry) == {"f": "answer"}


def test_a_split_never_gives_one_item_a_figure_another_calls_its_answer(seeded, cold):
    from learnloop.content.authoring import exercise_authoring as EX
    from learnloop.content.authoring.ai_contracts import ExerciseAuthoring
    from tests.test_exercise_authoring import FakeClient, _item, _write_facet_registry

    paths, ctx, repository = seeded
    _write_facet_registry(paths.root.parent)
    raw = {"nodes": [{"spanId": span, "quote": _text(span)} for span in ("q1", "g1", "d1")]}
    client = FakeClient(ExerciseAuthoring(items=[
        _item(statement_md="Estimate f(2) from the graph.", title="Exercise 1",
              figure_roles=[FigureRolePayload(span_id="g1", role="stimulus")]),
        _item(statement_md="Draw the diagram of the circuit with its equivalent resistance marked.",
              title="Exercise 2", figure_roles=[FigureRolePayload(span_id="g1", role="answer")]),
    ]))
    first, second = (summary["practice_item_id"] for summary in EX.import_exercises(
        paths.root, repository, client, extraction_id=EXT, raw_selection=raw, source_id="src_rd")["items"])
    assert _refs(paths, first)["g1"]["figure_role_rejected"] == "another_exercise_answer"
    assert _refs(paths, second)["g1"]["owned"] is False and _refs(paths, second)["g1"]["figure_role"] == "answer"
    assert _view(ctx, first)["kind"] == "none" and _view(ctx, second)["kind"] == "none"


# -- Sol verify 1: every claim on a figure counts, in any order --------------------------------------------


@pytest.mark.parametrize("claims", [["unrelated", "answer"], ["answer", "unrelated"], ["unrelated", "worked"],
                                    ["stimulus", "unrelated", "answer"]])
def test_a_duplicate_answer_claim_is_never_lost(claims):
    from learnloop.content.authoring.exercise_authoring import _answer_figures, _claimed_roles
    from tests.test_exercise_authoring import _item

    entry = _item(figure_roles=[FigureRolePayload(span_id="f", role=role) for role in claims])
    assert _claimed_roles(entry) == {"f": "worked" if "worked" in claims else "answer"}
    assert _answer_figures([entry, _item(figure_roles=[FigureRolePayload(span_id="f", role="stimulus")])]) == {"f"}


@pytest.mark.parametrize("claims", [["unrelated", "answer"], ["answer", "unrelated"], ["unrelated", "worked"]])
def test_a_sibling_never_owns_a_figure_one_item_calls_its_answer_among_duplicates(seeded, cold, claims):
    from learnloop.content.authoring import exercise_authoring as EX
    from learnloop.content.authoring.ai_contracts import ExerciseAuthoring
    from tests.test_exercise_authoring import FakeClient, _item, _write_facet_registry

    paths, ctx, repository = seeded
    _write_facet_registry(paths.root.parent)
    raw = {"nodes": [{"spanId": span, "quote": _text(span)} for span in ("q1", "g1", "d1")]}
    client = FakeClient(ExerciseAuthoring(items=[
        _item(statement_md="Draw the diagram of the circuit with its equivalent resistance marked.",
              title="Exercise 2", figure_roles=[FigureRolePayload(span_id="g1", role=role) for role in claims]),
        _item(statement_md="Estimate f(2) from the graph.", title="Exercise 1",
              figure_roles=[FigureRolePayload(span_id="g1", role="stimulus")]),
    ]))
    first, second = (summary["practice_item_id"] for summary in EX.import_exercises(
        paths.root, repository, client, extraction_id=EXT, raw_selection=raw, source_id="src_rd")["items"])
    assert _view(ctx, second)["kind"] == "none"                          # the sibling's stimulus claim is refused
    assert _refs(paths, second)["g1"]["owned"] is False
    assert _refs(paths, second)["g1"]["figure_role_rejected"] == "another_exercise_answer"
    assert _refs(paths, first)["g1"]["owned"] is False


# -- Sol verify 2: a figure never leaves by the words its text starts with ---------------------------------


def test_a_graph_titled_solution_concentration_shows_in_a_check_on_your_own(seeded, cold):
    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["c9", "g9"], "Estimate the concentration at t = 5 s from the graph.",
                              "about 0.4 mol/L", roles={"g9": "stimulus"})
    view = _view(ctx, item_id)
    assert view["kind"] == "figure" and len(view["crops"]) == 1
    assert _share(_image(view["crops"][0]["image"]), GREEN) > 0.9


def test_the_graph_titled_solution_concentration_prints_with_the_problem(seeded, warm):
    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["c9", "g9"], "Estimate the concentration at t = 5 s from the graph.",
                              "about 0.4 mol/L", roles={"g9": "stimulus"})
    assert _crop_spans(_view(ctx, item_id)) == [["c9"], ["g9"]]


def test_a_legacy_graph_titled_solution_concentration_still_shows_cold(seeded, cold):
    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["c9", "g9"], "Estimate the concentration at t = 5 s from the graph.",
                              "about 0.4 mol/L")
    _as_legacy(paths, item_id)
    assert _view(ctx, item_id)["kind"] == "figure"                       # main's answer, kept


@pytest.mark.parametrize(("text", "kind"), [
    ("Solution", "solution"), ("Solution.", "solution"), ("Solution: x = 2", "solution"),
    ("Solution. The sum is 4.", "solution"), ("Solutions 3.2:", "solution"), ("Solution (a).", "solution"),
    ("Solution\nThe sum is 4.", "solution"), ("Proof.", "proof"), ("Proof", "proof"),
    ("Solution concentration (mol/L) versus time (s).", None), ("Solutions of x^2 = 4 are 2 and -2.", None),
    ("Proofreading is a skill.", None), ("Find the solution.", None),
])
def test_a_solution_lead_is_a_heading_not_a_word_starting_a_sentence(text, kind):
    from learnloop.reader.as_printed import _answer_heading

    assert _answer_heading(text) == kind


# -- Sol verify 3: no crop shows excluded pixels where boxes overlap --------------------------------------


def test_an_overlapping_figure_box_over_another_figures_excluded_rest_gives_no_free_crop(seeded, warm):
    """Sol verify 3 probe, under the ruling: Figure 4's box overlaps the rest
    of Figure 3's box the learner's sub-box leaves out (the inset), so the
    free crop is withheld and the page offered (rewritten: it pinned masks)."""

    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["t8", "fa", "fb"], "Compare Figure 3 with Figure 4.", "one curves",
                              roles={"fa": "stimulus", "fb": "stimulus"}, region=FA_REGION)
    _no_free_crop(_view(ctx, item_id), "t8")


def test_in_a_check_on_your_own_both_figures_stay_whole(seeded, cold):
    """The problem stays answerable: each retained figure shows its own area
    whole. The residual (the review's): the inset lies inside Figure 4's own
    box, so it shows in that figure's crop."""

    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["t8", "fa", "fb"], "Compare Figure 3 with Figure 4.", "one curves",
                              roles={"fa": "stimulus", "fb": "stimulus"}, region=FA_REGION)
    view = _view(ctx, item_id)
    assert view["kind"] == "figure" and len(view["crops"]) == 2
    first, second = (_image(crop["image"]) for crop in view["crops"])
    assert _share(first, GREEN) > 0.9 and _share(first, BLUE) == 0      # Figure 3: its sub-box only
    assert _share(second, GREEN) > 0.9


def test_a_box_overlapping_a_dropped_solution_block_gives_no_free_crop(seeded, warm):
    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["p8", "r8"], "Compute 5+5.", "10")
    _no_free_crop(_view(ctx, item_id), "p8")


# -- the Sol verify ruling: one rule for overlapping boxes ------------------------------------------------


def _enclosed(paths, repository, monkeypatch, page: int) -> str:
    """The problem P{page} selected with the box E{page} that encloses it,
    E excluded for that page's reason."""

    number = _text(f"P{page}").split("Compute ", 1)[1].rstrip(".")
    roles = {8 + 3: {f"E{page}": "answer"}, 8 + 4: {f"E{page}": "worked"}}.get(page)
    item_id, _calls = _import(paths, repository, [f"P{page}", f"E{page}"], f"Compute {number}.", "even",
                              roles=roles)
    if page == 8:
        _record_solution(paths, repository, item_id, [f"P{page}", f"E{page}"], [f"E{page}"])
    if page == 9:
        import learnloop_sidecar.handlers.as_printed as handler

        real = handler.block_roles

        def roles_with_solution(connection, keys):
            found = dict(real(connection, keys))
            found.update({key: "solution" for key in keys if key[1] == f"E{page}"})
            return found

        monkeypatch.setattr(handler, "block_roles", roles_with_solution)
    return item_id


@pytest.mark.parametrize("page", [8, 9, 10, 11, 12],
                         ids=["solution_span", "solution_role", "solution_heading", "answer_figure", "worked_figure"])
def test_a_problem_inside_an_excluded_box_gets_no_free_crop(seeded, warm, monkeypatch, page):
    paths, ctx, repository = seeded
    item_id = _enclosed(paths, repository, monkeypatch, page)
    view = _view(ctx, item_id)
    _no_free_crop(view, f"P{page}")                                      # no crop: no answer pixel anywhere


@pytest.mark.parametrize("page", [8, 10, 11])
def test_and_a_check_on_your_own_shows_nothing_of_it(seeded, cold, monkeypatch, page):
    paths, ctx, repository = seeded
    item_id = _enclosed(paths, repository, monkeypatch, page)
    assert _view(ctx, item_id)["kind"] == "none"                         # the retained problem is text


def test_a_retained_figure_under_another_figures_excluded_rest_shows_whole_in_a_check(seeded, cold):
    """Sol verify (c): Figure 5's unselected rest covers retained Figure 6.
    Retained content is never painted, so Figure 6 shows whole."""

    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["ta", "fA", "fB"], "Compare Figure 5 with Figure 6.", "one curves",
                              roles={"fA": "stimulus", "fB": "stimulus"}, region=A_REGION)
    view = _view(ctx, item_id)
    assert view["kind"] == "figure" and len(view["crops"]) == 2
    assert all(_share(_image(crop["image"]), GREEN) > 0.9 for crop in view["crops"])


def test_and_outside_a_check_the_rule_withholds_the_free_crop(seeded, warm):
    from learnloop.reader.as_printed import shows_unsafe

    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["ta", "fA", "fB"], "Compare Figure 5 with Figure 6.", "one curves",
                              roles={"fA": "stimulus", "fB": "stimulus"}, region=A_REGION)
    blocks = repository.document_blocks(EXT, ["ta", "fA", "fB"])
    on_page = repository.document_blocks_on_pages(EXT, [6])
    assert shows_unsafe(blocks, on_page, set(), {"fA": (6, (0.0, 100.0, 100.0, 200.0))})   # U ∩ R is not empty
    _no_free_crop(_view(ctx, item_id), "ta")


def test_a_scale_label_over_a_graph_is_neutral_and_the_graph_stays(seeded, warm):
    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["s7", "gp"], "Read y at x = 2 from the plot.", "4",
                              roles={"gp": "stimulus"})
    view = _view(ctx, item_id)
    assert _crop_spans(view) == [["s7"], ["gp"]]
    graph = _image(view["crops"][1]["image"])
    assert _share(graph, GREEN) > 0.8 and _share(graph, GREY) > 0      # the label is kept, never painted


def test_and_in_a_check_on_your_own(seeded, cold):
    paths, ctx, repository = seeded
    item_id, _calls = _import(paths, repository, ["s7", "gp"], "Read y at x = 2 from the plot.", "4",
                              roles={"gp": "stimulus"})
    view = _view(ctx, item_id)
    assert view["kind"] == "figure" and _share(_image(view["crops"][0]["image"]), GREEN) > 0.8


# -- Sol verify of 788241756: one predicate for an unsafe figure -------------------------------------------


def _sibling_answer_import(paths, repository) -> str:
    from learnloop.content.authoring import exercise_authoring as EX
    from learnloop.content.authoring.ai_contracts import ExerciseAuthoring
    from tests.test_exercise_authoring import FakeClient, _item, _write_facet_registry

    _write_facet_registry(paths.root.parent)
    raw = {"nodes": [{"spanId": span, "quote": _text(span)} for span in ("tq", "fs", "fx", "tz")]}
    client = FakeClient(ExerciseAuthoring(items=[
        _item(statement_md="Find the slope of the line in Figure 7.", title="Exercise 1",
              figure_roles=[FigureRolePayload(span_id="fs", role="stimulus"),
                            FigureRolePayload(span_id="fx", role="stimulus")]),
        _item(statement_md="Sketch the completed graph.", title="Exercise 2",
              figure_roles=[FigureRolePayload(span_id="fx", role="answer")]),
    ]))
    first, _second = (summary["practice_item_id"] for summary in EX.import_exercises(
        paths.root, repository, client, extraction_id=EXT, raw_selection=raw, source_id="src_rd")["items"])
    return first


def test_a_siblings_answer_overlapping_a_retained_figure_gives_no_free_crop(seeded, warm):
    paths, ctx, repository = seeded
    item_id = _sibling_answer_import(paths, repository)
    ref = _refs(paths, item_id)["fx"]
    assert (ref["figure_role"], ref["figure_role_rejected"], ref["owned"]) == (
        "stimulus", "another_exercise_answer", False)
    view = _view(ctx, item_id)
    _no_free_crop(view, "tq")                                            # no crop: 0 answer pixels


def test_and_a_check_on_your_own_keeps_the_problems_figure(seeded, cold):
    paths, ctx, repository = seeded
    view = _view(ctx, _sibling_answer_import(paths, repository))
    assert view["kind"] == "figure" and len(view["crops"]) == 1         # answerable (the residual: fx's ink in fs's box)


def test_every_rejection_reason_the_validator_emits_is_classified():
    import inspect
    import itertools

    from learnloop.content.authoring import exercise_authoring as EX
    from learnloop.ingest.block_roles import FIGURE_REJECTION_UNSAFE, figure_is_unsafe

    emitted: set[str] = set()
    figures = {"n": "Figure 2. A graph.", "u": "A graph."}
    for statement, elsewhere, role in itertools.product(
            ("Use Figure 1.", "Use the graph.", "Use Figure 2."), (set(), {"n"}, {"u"}, {"n", "u"}),
            ("stimulus", "answer", "worked", "unrelated")):
        for _role, rejected in EX._figure_roles({"n": role, "u": role}, figures, statement,
                                                claimed_elsewhere=elsewhere).values():
            if rejected is not None:
                emitted.add(rejected)
    assert emitted == set(FIGURE_REJECTION_UNSAFE)                       # every reason it emits is classified
    # ...and the validator names no reason outside the shared table.
    assert 'rejected = "' not in inspect.getsource(EX._figure_roles)
    assert all(figure_is_unsafe("stimulus", reason) for reason in FIGURE_REJECTION_UNSAFE)
    assert figure_is_unsafe("stimulus", "a_reason_added_later")         # an unclassified reason fails closed
    assert figure_is_unsafe("answer", None) and figure_is_unsafe("worked", None)
    assert not figure_is_unsafe("stimulus", None) and not figure_is_unsafe("unrelated", None)
