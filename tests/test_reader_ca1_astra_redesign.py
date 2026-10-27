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
)
#: F6: the answer inset inside h1's block, and the learner's sub-box of h1 leaving it out.
INSET = (2, [80.0, 180.0, 100.0, 210.0])
H1_REGION = {"spanId": "h1", "page": 2, "bbox": [10.0, 120.0, 40.0, 150.0]}


def _seed(root, repository) -> None:
    pages = []
    for page in range(4):
        image = Image.new("RGB", (612, 792), "white")
        draw = ImageDraw.Draw(image)
        for _span, _kind, block_page, bbox, colour, _text in LAYOUT:
            if block_page == page:
                draw.rectangle(bbox, fill=colour)
        if page == INSET[0]:
            draw.rectangle(INSET[1], fill=BLUE)
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
                        page_end=3, span_ids=[block.span_id for block in blocks])
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
