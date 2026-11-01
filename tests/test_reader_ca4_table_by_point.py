"""Reader CA4: the table by point (ux_reader_compare_ask_v1 §5, X3-X5, §12.2; K13).

* ``compare_sources(by_point=True)`` asks ``source_compare.v2`` on the same
  route in one call: points with labels; per source a cell, the book's
  verified words and LearnLoop's line, or ``not_addressed``; per point its
  pairs' relations from the unchanged ``RELATIONS``; requested perspectives
  as points in the learner's words. Every cell's quote is verified in code: a
  cell that fails is not addressed (listed as dropped), a relation needs two
  quoted cells of its point, a point no book quotes is dropped unless it is a
  perspective ("not found in your library"). No consensus field.
* Stored in ``source_comparisons.comparison_json`` (no migration), cached
  under its own identity; a v1 row is never reused for it.
* Keep maps a kept row to today's proposals, one claim per cell with the
  row's label in ``content_json``; takes on a row or on the whole comparison;
  a hidden row is left out before Keep and superseded after it, and showing
  it proposes it again.
* ``reader_compare.by_point`` off: the Reader requests v1 and the table, the
  contract and the keep are today's; ``max_perspectives`` is a config key.

Every model is a fake (no network).
"""
from __future__ import annotations

from contextlib import closing
import json
from typing import Any

import pytest

from learnloop.db.connection import connect
from learnloop.db.stores.source_block_fts import blocks_by_key
from learnloop.source_retrieval import kept_comparisons as KC
from learnloop.source_retrieval.compare import (
    COMPARE_PROMPT_VERSION_V2,
    RELATIONS,
    ComparisonPoint,
    PairRelation,
    PointCell,
    SourceComparisonV2,
    _verified_points,
    compare_sources,
)
from learnloop.source_retrieval.policy import CallerContext
from learnloop.source_retrieval.search import SpanHit
from learnloop_sidecar.errors import SidecarError
from tests.library_ask_fixtures import ask_rows, build_library_vault, call, context, set_config
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, loaded

QUESTION = "why does the determinant change sign when two rows are swapped"
PINS = ["ext_book:s6", "ext_text:t3"]


def _rows(repository, sql: str, *args) -> list[dict[str, Any]]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        connection.row_factory = __import__("sqlite3").Row
        return [dict(row) for row in connection.execute(sql, args)]


def _fake_service(monkeypatch, llm=None):
    import learnloop.instructional.sources as service

    real = service.propose_comparison
    llm = llm or FakeServiceLLM()
    seen: list[dict[str, Any]] = []

    def bound(*args, **kwargs):
        seen.append(dict(kwargs))
        return real(*args, client=llm, verify_client=llm, **kwargs)

    monkeypatch.setattr(service, "propose_comparison", bound)
    return llm, seen


def _ask(ctx) -> dict[str, Any]:
    return call(ctx, "reader.library_ask", {"query": QUESTION, "extractionId": "ext_text", "spanIds": ["t3"],
                                            "learningObjectIds": ["lo_matrices"]})


@pytest.fixture
def library(tmp_path, monkeypatch):
    paths, repository, spans = build_library_vault(tmp_path / "vault")
    ctx = context(paths.root)
    llm, seen = _fake_service(monkeypatch)
    return paths, ctx, repository, llm, seen


def _compared(library, **extra):
    paths, ctx, repository, llm, seen = library
    asked = _ask(ctx)
    table = call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": PINS, **extra})
    assert table["status"] == "ok" and table["comparisonId"], table
    return asked, table


def _kept_json(repository, ask_id: str) -> dict[str, Any]:
    row = next(r for r in ask_rows(repository) if r["id"] == ask_id)
    return json.loads(row["kept_json"])


def _quoted(point: dict[str, Any]) -> list[dict[str, Any]]:
    return [cell for cell in point["cells"] if cell["status"] == "quoted"]


# -- the v2 contract: the schema has no consensus, every cell is verified ----------------------------------


def test_the_v2_schema_has_points_cells_and_relations_and_no_consensus_field():
    assert set(SourceComparisonV2.model_fields) == {"points"}
    assert set(ComparisonPoint.model_fields) == {"label", "perspective", "cells", "relations"}
    assert set(PointCell.model_fields) == {"source_ref", "status", "quote", "line"}
    # The relations are v1's set, unchanged: no "complementary".
    relation = PairRelation.model_fields["relation"].annotation
    assert set(relation.__args__) == set(RELATIONS) and "complementary" not in RELATIONS
    for model in (SourceComparisonV2, ComparisonPoint, PointCell):
        assert not {name for name in model.model_fields if "consensus" in name or "summary" in name
                    or "overall" in name or "canonical" in name}


def _hit(ref: str, text: str) -> SpanHit:
    return SpanHit(extraction_id=f"ext_{ref}", span_id="b1", source_id=f"src_{ref}", source_title=ref.title(),
                   text=text, block_type="Text", section_path=[], page=1, ordinal=1, ranks={})


PASSAGES = {
    "s1": "Swapping two rows of a matrix multiplies its determinant by minus one, always.",
    "s2": "The determinant is alternating: exchanging two rows reverses its sign in every case.",
    "s3": "A third book says nothing on rows at all but defines volume forms carefully.",
}


def _verify(points: list[ComparisonPoint], requested: list[str] = ()) -> tuple[list[dict], list[dict]]:
    refs = {ref: _hit(ref, text) for ref, text in PASSAGES.items()}
    holders = {ref: [(hit.extraction_id, hit.span_id, hit.text)] for ref, hit in refs.items()}
    dropped: list[dict[str, Any]] = []
    shown = _verified_points(SourceComparisonV2(points=points), refs, dict(PASSAGES), holders, list(requested),
                             dropped)
    return shown, dropped


def _cell(ref: str, quote: str | None = None, line: str = "its reading") -> PointCell:
    if quote is None:
        return PointCell(source_ref=ref, status="not_addressed", quote="", line="")
    return PointCell(source_ref=ref, status="quoted", quote=quote, line=line)


def test_every_cells_quote_is_verified_in_code_and_a_failed_one_is_not_addressed():
    shown, dropped = _verify([ComparisonPoint(label="the sign rule", perspective="", relations=[], cells=[
        _cell("s1", "multiplies its determinant by minus one"),
        _cell("s2", "words that are nowhere in the passage"),
        _cell("s9", "no such source here at all"),
    ])])
    (point,) = shown
    assert point["id"] == "p1" and point["label"] == "the sign rule" and point["kind"] == "point"
    cells = {cell["ref"]: cell for cell in point["cells"]}
    # One cell per compared source, in column order; a missing one is not addressed.
    assert [cell["ref"] for cell in point["cells"]] == ["s1", "s2", "s3"]
    assert cells["s1"]["status"] == "quoted" and cells["s1"]["span_key"] == "ext_s1:b1"
    assert cells["s2"] == {"ref": "s2", "status": "not_addressed"}
    assert cells["s3"] == {"ref": "s3", "status": "not_addressed"}
    reasons = {(entry["kind"], entry.get("source_ref")): entry["reason"] for entry in dropped}
    assert reasons[("cell", "s2")] == "its quote is not in that source's passage"
    assert ("cell", "s9") in reasons
    # Never repaired: the failed cell carries no quote and no line.
    assert "quote" not in cells["s2"] and "line" not in cells["s2"]


def test_a_relation_stands_only_between_two_quoted_cells_of_its_point():
    good = PairRelation(left_ref="s1", right_ref="s2", relation="different_notation", statement="same rule",
                        left_quote="multiplies its determinant by minus", right_quote="exchanging two rows reverses")
    to_unquoted = PairRelation(left_ref="s1", right_ref="s3", relation="disagreement", statement="no",
                               left_quote="multiplies its determinant by minus", right_quote="defines volume forms carefully")
    duplicate = PairRelation(left_ref="s2", right_ref="s1", relation="equivalent", statement="again",
                             left_quote="exchanging two rows reverses", right_quote="multiplies its determinant by minus")
    bad_quote = PairRelation(left_ref="s1", right_ref="s2", relation="unclear", statement="x",
                             left_quote="multiplies its determinant by minus", right_quote="not in the passage at all")
    shown, dropped = _verify([ComparisonPoint(label="the sign rule", perspective="", cells=[
        _cell("s1", "multiplies its determinant by minus one"), _cell("s2", "exchanging two rows reverses its sign"),
        _cell("s3")], relations=[bad_quote, good, to_unquoted, duplicate])])
    (point,) = shown
    assert [(rel["left_ref"], rel["right_ref"], rel["relation"]) for rel in point["relations"]] == [
        ("s1", "s2", "different_notation")]
    assert sum(1 for entry in dropped if entry["kind"] == "relation") == 3


def test_perspectives_are_points_in_the_learners_words_and_one_no_book_fills_is_kept_as_not_found():
    shown, dropped = _verify([
        ComparisonPoint(label="nobody quotes this", perspective="", relations=[], cells=[_cell("s1"), _cell("s2")]),
        ComparisonPoint(label="Geometric picture (model)", perspective="A GEOMETRIC VIEW", relations=[],
                        cells=[_cell("s2", "exchanging two rows reverses its sign")]),
        ComparisonPoint(label="geometric again", perspective="a geometric view", relations=[],
                        cells=[_cell("s1", "multiplies its determinant by minus one")]),
        ComparisonPoint(label="", perspective="", relations=[], cells=[_cell("s1", "multiplies its determinant by")]),
    ], requested=["a geometric view", "an application"])
    labels = [(point["label"], point["kind"]) for point in shown]
    # The model's points first (a point no book quotes is dropped; a second
    # point for one perspective is an ordinary point), then the learner's
    # views in their order and in their words.
    assert labels == [("geometric again", "point"), ("a geometric view", "perspective"),
                      ("an application", "perspective")]
    assert [point["id"] for point in shown] == ["p1", "p2", "p3"]
    application = shown[2]
    assert not _quoted(application) and len(application["cells"]) == 3
    assert {entry["reason"] for entry in dropped if entry["kind"] == "point"} == {
        "no book's words on it were found", "it has no label"}


# -- compare_sources by point, stored, cached apart -------------------------------------------------------------


@pytest.fixture
def textbook(tmp_path):
    return build_textbook_vault(tmp_path / "vault")


def test_compare_sources_by_point_is_one_call_on_the_same_route_and_stores_v2(textbook):
    paths, repository, _spans = textbook
    llm = FakeServiceLLM()
    result = compare_sources(loaded(paths), repository, QUESTION, caller=CallerContext(kind="reader"),
                             requested_perspectives=["a geometric view", "an application"], by_point=True,
                             client=llm, verify_client=llm)
    assert result.status == "ok" and result.manifest["contract"] == COMPARE_PROMPT_VERSION_V2
    assert [purpose for purpose, model in llm.calls if model.startswith("SourceComparison")] == ["source_compare"]
    assert ("source_compare", "SourceComparisonV2") in llm.calls
    labels = [(point["label"], point["kind"]) for point in result.points]
    assert labels == [("the main claim", "point"), ("what the first book adds", "point"),
                      ("a geometric view", "perspective"), ("an application", "perspective")]
    main = result.points[0]
    assert len(_quoted(main)) == len(result.sources) >= 2
    assert {rel["relation"] for rel in main["relations"]} == {"different_notation"}
    assert len(_quoted(result.points[1])) == 1
    assert result.missing_perspectives == ["an application"]
    payload = result.as_dict()
    assert payload["contract"] == COMPARE_PROMPT_VERSION_V2 and payload["points"] == result.points
    stored = _rows(repository, "SELECT * FROM source_comparisons WHERE id = ?", result.comparison_id)[0]
    assert stored["prompt_version"] == COMPARE_PROMPT_VERSION_V2
    comparison = json.loads(stored["comparison_json"])
    assert comparison["contract"] == COMPARE_PROMPT_VERSION_V2 and comparison["points"] == result.points
    # Every v1 reader reads it unchanged: each quoted cell is its source's
    # contribution and each point's relation a relation, naming its point.
    for entry in comparison["sources"]:
        assert entry["contributions"] and all(line["point_id"] for line in entry["contributions"])
    assert comparison["relations"] and all(rel["point_id"] == "p1" for rel in comparison["relations"])
    for point in result.points:
        for cell in _quoted(point):
            passage = next(entry["passage"] for entry in comparison["sources"] if entry["ref"] == cell["ref"])
            assert cell["quote"] in passage


def test_a_v2_request_never_reuses_a_v1_row_and_reuses_its_own(textbook):
    paths, repository, _spans = textbook
    llm = FakeServiceLLM()
    v1 = compare_sources(loaded(paths), repository, QUESTION, caller=CallerContext(kind="reader"),
                         client=llm, verify_client=llm)
    v2 = compare_sources(loaded(paths), repository, QUESTION, caller=CallerContext(kind="reader"), by_point=True,
                         client=llm, verify_client=llm)
    assert v1.points is None and "points" not in v1.as_dict() and "contract" not in v1.as_dict()
    assert v2.reused is False and v2.comparison_id != v1.comparison_id and v2.points
    again = compare_sources(loaded(paths), repository, QUESTION, caller=CallerContext(kind="reader"), by_point=True,
                            client=llm, verify_client=llm)
    assert again.reused is True and again.comparison_id == v2.comparison_id and again.points == v2.points
    v1_again = compare_sources(loaded(paths), repository, QUESTION, caller=CallerContext(kind="reader"),
                               client=llm, verify_client=llm)
    assert v1_again.reused is True and v1_again.comparison_id == v1.comparison_id and v1_again.points is None


def test_an_invented_quote_is_dropped_never_shown(textbook):
    paths, repository, _spans = textbook
    llm = FakeServiceLLM(bad_comparison_quote=True)
    result = compare_sources(loaded(paths), repository, QUESTION, caller=CallerContext(kind="reader"), by_point=True,
                             client=llm, verify_client=llm)
    assert "an invented point" not in {point["label"] for point in result.points}
    assert any(entry["kind"] == "cell" for entry in result.dropped_lines)
    assert any(entry["kind"] == "point" for entry in result.dropped_lines)


class LaterBlockLLM(FakeServiceLLM):
    """Quotes the last words of each passage (an anchor's later block)."""

    def _SourceComparisonV2(self, request, context):
        sources = context["sources"]
        cells = [PointCell(source_ref=src["ref"], status="quoted", quote=" ".join(src["passage"].split()[-5:]),
                           line="ends its way") for src in sources]
        return SourceComparisonV2(points=[ComparisonPoint(label="the ending", perspective="", cells=cells,
                                                          relations=[])])


def test_a_cell_names_the_anchor_block_that_holds_its_quote(textbook):
    paths, repository, _spans = textbook
    with repository.connection() as connection:
        first, second = [row[0] for row in connection.execute(
            "SELECT span_id FROM source_document_blocks WHERE extraction_id = 'ext_text' AND block_type = 'Text' "
            "ORDER BY ordinal LIMIT 2")]
    llm = LaterBlockLLM()
    result = compare_sources(loaded(paths), repository, QUESTION, caller=CallerContext(kind="reader"), by_point=True,
                             anchor_span_keys=[f"ext_text:{first}", f"ext_text:{second}"], client=llm,
                             verify_client=llm)
    (point,) = result.points
    anchor = next(cell for cell in point["cells"] if cell["ref"] == "s1")
    assert anchor["status"] == "quoted" and anchor["span_key"] == f"ext_text:{second}"
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        text = blocks_by_key(connection, [("ext_text", second)])[("ext_text", second)].text
    assert anchor["quote"] in text


def test_a_quote_across_two_anchor_blocks_is_not_shown_as_one_blocks_words(textbook):
    """Codex review F5: a quote verified against the joined anchor but held by
    neither block alone names no block (Peek/Open would show part of it and
    Keep could not cite it): the cell is not addressed and listed as dropped."""

    paths, repository, _spans = textbook
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        first, second = [row[0] for row in connection.execute(
            "SELECT span_id FROM source_document_blocks WHERE extraction_id = 'ext_text' AND block_type = 'Text' "
            "ORDER BY ordinal LIMIT 2")]
        blocks = blocks_by_key(connection, [("ext_text", first), ("ext_text", second)])
    across = " ".join(blocks[("ext_text", first)].text.split()[-3:] + blocks[("ext_text", second)].text.split()[:3])

    class CrossBlockLLM(FakeServiceLLM):
        def _SourceComparisonV2(self, request, context):
            cells = [PointCell(source_ref=src["ref"], status="quoted", line="joins them",
                               quote=across if across in " ".join(src["passage"].split())
                               else " ".join(src["passage"].split()[:5])) for src in context["sources"]]
            return SourceComparisonV2(points=[ComparisonPoint(label="the seam", perspective="", cells=cells,
                                                              relations=[])])

    llm = CrossBlockLLM()
    result = compare_sources(loaded(paths), repository, QUESTION, caller=CallerContext(kind="reader"), by_point=True,
                             anchor_span_keys=[f"ext_text:{first}", f"ext_text:{second}"], client=llm,
                             verify_client=llm)
    anchor = next(cell for point in result.points for cell in point["cells"] if cell["ref"] == "s1")
    assert anchor["status"] == "not_addressed"
    assert any(entry["kind"] == "cell" and entry["source_ref"] == "s1" for entry in result.dropped_lines)


# -- the Reader: the table by point, v1 compatibility, the switch ---------------------------------------------


def test_the_readers_comparison_is_by_point_with_columns_by_book(library):
    paths, ctx, repository, _llm, seen = library
    contract = call(ctx, "reader.prompt_contract", {})
    assert contract["libraryAsk"]["compareByPoint"] is True
    asked, table = _compared(library, requestedPerspectives=["a geometric view"])
    assert seen[-1]["by_point"] is True
    assert table["contract"] == COMPARE_PROMPT_VERSION_V2
    columns = [row["key"] for row in table["rows"]]
    assert len(columns) == 2 and "ext_text:t3" in columns
    for point in table["points"]:
        assert [cell["key"] for cell in point["cells"]] == columns
        for cell in point["cells"]:
            assert cell["status"] in ("quoted", "not_addressed")
            if cell["status"] == "quoted":
                assert cell["quote"] and cell["line"] and cell["spanKey"]
        for relation in point["relations"]:
            assert relation["leftKey"] in columns and relation["rightKey"] in columns
            assert relation["relation"] in RELATIONS
    view = next(point for point in table["points"] if point["kind"] == "perspective")
    assert view["label"] == "a geometric view" and view["labelVoice"] == "learner"
    assert {point["labelVoice"] for point in table["points"] if point["kind"] == "point"} == {"model"}
    # The by-book view stays in the same table: each book's cells as its contributions.
    assert all(row["contributes"] for row in table["rows"])


def test_switched_off_the_reader_requests_v1_and_renders_by_book_exactly(tmp_path, monkeypatch):
    tables = {}
    _llm, seen = _fake_service(monkeypatch)
    for name, on in (("on", True), ("off", False)):
        paths, repository, _spans = build_library_vault(tmp_path / name)
        if not on:
            set_config(paths, "reader_compare", by_point=False)
        ctx = context(paths.root)
        asked = _ask(ctx)
        table = call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": PINS})
        tables[name] = (table, seen[-1], call(ctx, "reader.prompt_contract", {}), repository)
    off, off_request, off_contract, off_repository = tables["off"]
    assert "by_point" not in off_request
    assert "points" not in off and "contract" not in off
    assert "compareByPoint" not in off_contract["libraryAsk"]
    stored = _rows(off_repository, "SELECT prompt_version, comparison_json FROM source_comparisons")
    assert [row["prompt_version"] for row in stored] == ["source_compare.v1"]
    assert "points" not in json.loads(stored[0]["comparison_json"])
    on = tables["on"][0]
    # Off is v1's table: the same keys as on, less the points.
    assert set(on) - set(off) == {"points", "contract"}


def test_a_v1_comparison_kept_before_ca4_reopens_by_book(tmp_path, monkeypatch):
    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    set_config(paths, "reader_compare", by_point=False)
    ctx = context(paths.root)
    _fake_service(monkeypatch)
    asked = _ask(ctx)
    call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": PINS})
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    # CA4 turned on: the old keep still opens, by book, with today's cells.
    text = (paths.root / "learnloop.toml").read_text(encoding="utf-8").replace("by_point = false", "by_point = true")
    (paths.root / "learnloop.toml").write_text(text, encoding="utf-8")
    reopened = call(context(paths.root), "reader.library_compare_reopen", {"askId": asked["askId"]})
    assert "points" not in reopened and reopened["rows"] and "layout" not in reopened["kept"]
    assert all(row["contributes"] for row in reopened["rows"])


# -- keep by point: one claim per cell ------------------------------------------------------------------------


def test_keep_maps_each_quoted_cell_to_one_claim_with_its_rows_label(library):
    _paths, ctx, repository, _llm, _seen = library
    asked, table = _compared(library)
    kept = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    quoted = [(point, cell) for point in table["points"] for cell in _quoted(point)]
    objects = _rows(repository, "SELECT * FROM source_objects")
    assert len(objects) == len(quoted)
    versions = _rows(repository, "SELECT * FROM source_object_versions")
    assert {(v["status"], v["authorship"]) for v in versions} == {("proposed", "ai")}
    by_point: dict[str, list[dict[str, Any]]] = {}
    for version in versions:
        content = json.loads(version["content_json"])
        assert content["kept_from"] == "source_comparison" and content["comparison_id"] == table["comparisonId"]
        point = content["point"]
        assert set(point) == {"id", "label", "kind"}
        by_point.setdefault(point["id"], []).append(version)
        label = next(p["label"] for p in table["points"] if p["id"] == point["id"])
        assert point["label"] == label
        assert version["exact_text"] in {cell["quote"] for p, cell in quoted if p["id"] == point["id"]}
    for point in table["points"]:
        assert len(by_point.get(point["id"], [])) == len(_quoted(point))
    relations = _rows(repository, "SELECT * FROM source_object_relations")
    assert len(relations) == sum(len(point["relations"]) for point in table["points"])
    assert {r["relation_type"] for r in relations} == {KC.RELATION_MAP["different_notation"]}
    stored = _kept_json(repository, asked["askId"])
    assert stored["layout"] == KC.BY_POINT_LAYOUT and stored["hidden_points"] == []
    assert sorted(stored["keys"]) == sorted(row["key"] for row in table["rows"])
    assert all(obj["cell"] == KC.cell_key(obj["key"], obj["point_id"]) for obj in stored["objects"])
    state = kept["kept"]
    assert state["layout"] == "by_point" and state["hiddenPoints"] == []
    assert {obj["pointId"] for obj in state["objects"]} == {point["id"] for point in table["points"] if _quoted(point)}
    # The marks and the card read it as any keep.
    assert call(ctx, "reader.kept_comparisons", {"extractionId": "ext_text"})["marks"]


def test_a_take_on_a_row_and_on_the_whole_comparison(library):
    _paths, ctx, repository, _llm, _seen = library
    asked, table = _compared(library, requestedPerspectives=["a geometric view", "an application"])
    main = table["points"][0]
    missing = next(point for point in table["points"] if point["label"] == "an application")
    # A row no book fills has nothing to hold a take: refused, nothing written.
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "takes": [
            {"text": "nothing here", "pointId": missing["id"]}]})
    assert caught.value.code == "validation_error"
    assert _rows(repository, "SELECT * FROM source_objects") == []
    kept = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "takes": [
        {"text": "Axler's route generalizes", "pointId": main["id"]},
        {"text": "both books agree on the rule", "about": "comparison"}]})
    takes = {take.get("pointId") or take.get("about"): take for take in kept["kept"]["takes"]}
    assert set(takes) == {main["id"], "comparison"}
    learner = _rows(repository, "SELECT * FROM source_object_relations WHERE authorship = 'learner'")
    assert {r["learner_text"] for r in learner} == {"Axler's route generalizes", "both books agree on the rule"}
    stored = _kept_json(repository, asked["askId"])
    row_objects = {obj["id"] for obj in stored["objects"] if obj["point_id"] == main["id"]}
    row_take = next(r for r in learner if r["learner_text"] == "Axler's route generalizes")
    assert {row_take["source_object_id"], row_take["related_object_id"]} <= row_objects
    # Replayed (a retry after a lost response): nothing new.
    again = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "takes": [
        {"text": "Axler's route generalizes", "pointId": main["id"]}]})
    assert again["addedTakes"] == 0
    # A take names exactly one target.
    with pytest.raises(Exception):
        call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "takes": [
            {"text": "both", "pointId": main["id"], "about": "comparison"}]})


def test_a_row_hidden_before_keep_is_left_out(library):
    _paths, ctx, repository, _llm, _seen = library
    asked, table = _compared(library)
    hidden = table["points"][1]["id"]
    kept = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "hiddenPoints": [hidden]})
    stored = _kept_json(repository, asked["askId"])
    assert hidden not in {obj["point_id"] for obj in stored["objects"]}
    assert stored["hidden_points"] == [hidden] and kept["kept"]["hiddenPoints"] == [hidden]
    assert len(_rows(repository, "SELECT * FROM source_objects")) == len(_quoted(table["points"][0]))
    with pytest.raises(SidecarError):
        call(ctx, "reader.library_compare_keep", {"askId": table["askId"], "hiddenPoints": ["p99"]})


def test_a_take_waiting_on_a_hidden_row_goes_with_showing_it(library):
    """Codex review F2: the client keeps a hidden row's take out of Keep (Keep
    would refuse it: the row has nothing kept) and sends it with the request
    that shows the row again; the row is proposed again, then the take sits
    on its claims."""

    _paths, ctx, repository, _llm, _seen = library
    asked, table = _compared(library)
    main = table["points"][0]["id"]
    with pytest.raises(SidecarError):
        call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "hiddenPoints": [main],
                                                  "takes": [{"text": "mine", "pointId": main}]})
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "hiddenPoints": [main]})
    shown = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "hiddenPoints": [],
                                                      "takes": [{"text": "mine", "pointId": main}]})
    assert shown["kept"]["hiddenPoints"] == [] and shown["addedTakes"] == 1
    stored = _kept_json(repository, asked["askId"])
    take = next(entry for entry in stored["takes"] if entry.get("point_id") == main)
    assert take["learner_text"] == "mine"


def test_hiding_a_kept_row_supersedes_its_proposals_and_showing_it_proposes_it_again(library):
    _paths, ctx, repository, _llm, _seen = library
    asked, table = _compared(library)
    main = table["points"][0]["id"]
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "takes": [
        {"text": "my line on it", "pointId": main}]})
    before = _kept_json(repository, asked["askId"])
    row_objects = [obj["id"] for obj in before["objects"] if obj["point_id"] == main]
    row_relations = [rel["id"] for rel in before["relations"] if rel["point_id"] == main]
    assert row_objects and row_relations and before["takes"]
    counts = {name: len(_rows(repository, f"SELECT * FROM {name}"))
              for name in ("source_objects", "source_object_versions", "source_object_relations")}
    hidden = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "hiddenPoints": [main]})
    assert hidden["kept"]["hiddenPoints"] == [main]
    after = _kept_json(repository, asked["askId"])
    assert not {obj["id"] for obj in after["objects"]} & set(row_objects)
    assert after["relations"] == [] and after["takes"] == []
    # Append-only: a superseded version per claim, a superseded successor per relation and take; nothing deleted.
    assert len(_rows(repository, "SELECT * FROM source_objects")) == counts["source_objects"]
    assert len(_rows(repository, "SELECT * FROM source_object_versions")) == \
        counts["source_object_versions"] + len(row_objects)
    assert len(_rows(repository, "SELECT * FROM source_object_relations")) == \
        counts["source_object_relations"] + len(row_relations) + 1
    for object_id in row_objects:
        head = _rows(repository, "SELECT status FROM source_object_versions WHERE source_object_id = ? "
                                 "ORDER BY version_ordinal DESC LIMIT 1", object_id)[0]
        assert head["status"] == "superseded"
    lineage = KC.relation_lineage(repository)
    assert set(row_relations) <= set(lineage.values())
    # Shown again: proposed again from the stored comparison (new claims).
    shown = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "hiddenPoints": []})
    assert shown["kept"]["hiddenPoints"] == []
    again = _kept_json(repository, asked["askId"])
    new_objects = [obj["id"] for obj in again["objects"] if obj["point_id"] == main]
    assert len(new_objects) == len(row_objects) and not set(new_objects) & set(row_objects)
    assert [rel["point_id"] for rel in again["relations"]] == [main] * len(row_relations)
    # Remove supersedes the rest; the hidden-row history stays.
    call(ctx, "reader.library_compare_remove", {"askId": asked["askId"]})
    heads = _rows(repository, "SELECT v.status FROM source_object_versions v WHERE v.version_ordinal = "
                              "(SELECT MAX(version_ordinal) FROM source_object_versions w "
                              "WHERE w.source_object_id = v.source_object_id)")
    assert {head["status"] for head in heads} == {"superseded"}
    assert _kept_json(repository, asked["askId"])["hidden_rows"]


def test_reopening_a_keep_by_point_shows_what_was_kept_and_its_hidden_rows(library):
    paths, ctx, repository, _llm, _seen = library
    asked, table = _compared(library)
    hidden = table["points"][1]["id"]
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "hiddenPoints": [hidden]})
    reopened = call(ctx, "reader.library_compare_reopen", {"askId": asked["askId"]})
    assert reopened["contract"] == COMPARE_PROMPT_VERSION_V2
    assert [point["id"] for point in reopened["points"]] == [point["id"] for point in table["points"]]
    assert reopened["kept"]["hiddenPoints"] == [hidden]
    main = reopened["points"][0]
    assert len(_quoted(main)) == len(_quoted(table["points"][0]))
    assert main["relations"] == table["points"][0]["relations"]
    # Switched off, the same keep reopens by book (today's table).
    set_config(paths, "reader_compare", by_point=False)
    by_book = call(context(paths.root), "reader.library_compare_reopen", {"askId": asked["askId"]})
    assert "points" not in by_book and by_book["rows"]


def test_switched_off_a_hidden_row_sharing_a_quote_stays_hidden_by_book(tmp_path, monkeypatch):
    """Codex review F1: two rows quote the same sentence of one book with
    different lines; the second is hidden. Reopened by book (switch off),
    only the kept cell's line shows: the filter is the kept cell (its row and
    passage), not the quote's text."""

    class SameQuoteLLM(FakeServiceLLM):
        def _SourceComparisonV2(self, request, context):
            result = super()._SourceComparisonV2(request, context)
            first = result.points[1].cells[0]
            result.points[1].cells[0] = PointCell(source_ref=first.source_ref, status="quoted",
                                                  quote=result.points[0].cells[0].quote,
                                                  line="a different gloss on the same sentence")
            return result

    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    ctx = context(paths.root)
    _fake_service(monkeypatch, SameQuoteLLM())
    asked, table = _compared((paths, ctx, repository, None, None))
    main, hidden = table["points"][0], table["points"][1]
    assert _quoted(main)[0]["quote"] == _quoted(hidden)[0]["quote"]
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], "hiddenPoints": [hidden["id"]]})
    set_config(paths, "reader_compare", by_point=False)
    by_book = call(context(paths.root), "reader.library_compare_reopen", {"askId": asked["askId"]})
    lines = [entry["line"] for row in by_book["rows"] for entry in row["contributes"]]
    assert "a different gloss on the same sentence" not in lines
    assert len(lines) == len(_quoted(main))


def test_switched_off_rows_and_row_takes_are_refused(tmp_path, monkeypatch):
    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    set_config(paths, "reader_compare", by_point=False)
    ctx = context(paths.root)
    _fake_service(monkeypatch)
    asked = _ask(ctx)
    call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": PINS})
    for params in ({"hiddenPoints": ["p1"]}, {"takes": [{"text": "mine", "pointId": "p1"}]},
                   {"takes": [{"text": "mine", "about": "comparison"}]}):
        with pytest.raises(SidecarError) as caught:
            call(ctx, "reader.library_compare_keep", {"askId": asked["askId"], **params})
        assert caught.value.code == "reader_compare_by_point_disabled"
    assert _rows(repository, "SELECT * FROM source_objects") == []
    # Today's keep is untouched: one claim per source.
    call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    stored = _kept_json(repository, asked["askId"])
    assert "layout" not in stored and len(stored["objects"]) == 2


# -- max_perspectives: a keep config key ----------------------------------------------------------------------


def test_max_perspectives_is_a_keep_config_key(tmp_path, monkeypatch):
    from learnloop.params.parameter_registry import classify_config_path

    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    set_config(paths, "reader_compare", max_perspectives=2)
    ctx = context(paths.root)
    _llm, seen = _fake_service(monkeypatch)
    contract = call(ctx, "reader.prompt_contract", {})
    assert contract["compareKeep"]["maxPerspectives"] == 2
    asked = _ask(ctx)
    table = call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": PINS,
                                                 "requestedPerspectives": ["one view", "two view", "three view"]})
    assert seen[-1]["requested_perspectives"] == ["one view", "two view"]
    assert table["requestedPerspectives"] == ["one view", "two view"]
    assert KC.clean_perspectives(["a", "A", "b", "c"], limit=2) == ["a", "b"]
    rule = classify_config_path("reader_compare.max_perspectives")
    assert rule.kind == "structural"
